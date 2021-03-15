import operator
from functools import reduce

from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from drf_yasg import openapi
from drf_yasg.codecs import OpenAPICodecJson
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework import exceptions, permissions, viewsets
from rest_framework.decorators import action, api_view, authentication_classes, parser_classes, permission_classes
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.core.cache import cache
from django.db.models import Max, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import get_language, ugettext_lazy as _

from core.models import Entry, Relation
from core.schemas import ACTIVE_TYPES_LIST, get_jsonschema, get_schema
from core.schemas.entries.conference import ConferenceSchema
from core.schemas.entries.document import TYPES as DOCUMENT_TYPES, DocumentSchema
from core.schemas.entries.event import EventSchema
from core.skosmos import get_altlabel_collection, get_collection_members, get_preflabel
from general.drf.authentication import TokenAuthentication
from general.drf.filters import CaseInsensitiveOrderingFilter
from media_server.models import get_media_for_entry
from media_server.utils import get_free_space_for_user

from .serializers.entry import EntrySerializer
from .serializers.relation import RelationSerializer
from .yasg import (
    JSONAutoSchema,
    OpenAPICodecDRFJson,
    authorization_header_paramter,
    language_header_decorator,
    language_header_parameter,
)

SchemaView = get_schema_view(
    openapi.Info(
        title='Portfolio API',
        default_version=settings.REST_FRAMEWORK.get('DEFAULT_VERSION'),
        # description="",
        # terms_of_service="",
        # contact=openapi.Contact(email=""),
        # license=openapi.License(name=""),
    ),
    validators=['ssv'] if settings.DEBUG else None,
    public=False,
    # permission_classes=(permissions.IsAuthenticated,),
)


class PortfolioSchemaView(SchemaView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for r in self.renderer_classes:
            if hasattr(r, 'codec_class') and r.codec_class is OpenAPICodecJson:
                r.codec_class = OpenAPICodecDRFJson


no_ui_view = PortfolioSchemaView.without_ui(cache_timeout=0)
swagger_view = PortfolioSchemaView.with_ui('swagger', cache_timeout=0)
redoc_view = PortfolioSchemaView.with_ui('redoc', cache_timeout=0)


class StandardLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    # offset_query_param = 'skip'


class CountModelMixin:
    """Count a queryset."""

    @swagger_auto_schema(manual_parameters=[], responses={200: openapi.Response('')})
    @action(detail=False, filter_backends=[], pagination_class=None)
    def count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        content = {'count': queryset.count()}
        return Response(content)


class EntryFilter(FilterSet):
    type = CharFilter(field_name='type', lookup_expr='source__iexact')

    class Meta:
        model = Entry
        fields = ['type']


entry_ordering_fields = ('title', 'date_created', 'date_changed', 'published', 'type_source', 'type_de', 'type_en')


@method_decorator(
    swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'sort',
                openapi.IN_QUERY,
                required=False,
                description='Which field to use when ordering the results.',
                type=openapi.TYPE_STRING,
                enum=list(entry_ordering_fields) + [f'-{i}' for i in entry_ordering_fields],
            ),
            openapi.Parameter(
                'q', openapi.IN_QUERY, required=False, description='Search query', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'link_selection_for',
                openapi.IN_QUERY,
                required=False,
                description='Get link selection for a certain entry',
                type=openapi.TYPE_STRING,
            ),
        ]
    ),
    name='list',
)
class EntryViewSet(viewsets.ModelViewSet, CountModelMixin):
    """
    retrieve:
    Returns a certain entry.

    list:
    Returns a list of all entries for current user.

    create:
    Create a new entry for current user.

    update:
    Update a certain entry.

    partial_update:
    Partially update a certain entry.

    destroy:
    Delete a certain entry.

    count:
    Returns the number of entries.

    media:
    Return list of media objects for a certain entry.
    """

    serializer_class = EntrySerializer
    filter_backends = (
        DjangoFilterBackend,
        CaseInsensitiveOrderingFilter,
    )
    filterset_class = EntryFilter
    ordering_fields = entry_ordering_fields
    pagination_class = StandardLimitOffsetPagination
    swagger_schema = JSONAutoSchema

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'detailed',
                openapi.IN_QUERY,
                required=False,
                description='Get a detailed response',
                default=False,
                type=openapi.TYPE_BOOLEAN,
            ),
        ],
        responses={
            200: openapi.Response(''),
            403: openapi.Response('Access not allowed'),
            404: openapi.Response('Entry not found'),
        },
    )
    @action(detail=True, filter_backends=[], pagination_class=None)
    def media(self, request, pk=None, *args, **kwargs):
        try:
            entry = Entry.objects.get(pk=pk)
            if entry.owner != request.user:
                raise exceptions.PermissionDenied(_('Current user is not the owner of this entry'))
            ret = get_media_for_entry(entry.pk, flat=request.query_params.get('detailed') != 'true')
            return Response(ret)
        except Entry.DoesNotExist:
            raise exceptions.NotFound(_('Entry does not exist'))

    @swagger_auto_schema(responses={200: openapi.Response('')})
    @action(detail=False, filter_backends=[], pagination_class=None)
    def types(self, request, *args, **kwargs):
        language = get_language() or 'en'
        content = self.get_queryset().exclude(type__isnull=True).values_list('type', flat=True).distinct().order_by()
        return Response(sorted(content, key=lambda x: x.get('label', {}).get(language, '').lower()))

    def get_queryset(self):
        user = self.request.user
        qs = (
            Entry.objects.filter(owner=user)
            .annotate(
                type_source=KeyTextTransform('source', 'type'),
                type_de=KeyTextTransform('de', KeyTextTransform('label', 'type')),
                type_en=KeyTextTransform('en', KeyTextTransform('label', 'type')),
            )
            .order_by('-date_changed')
        )

        if self.action == 'list':
            q = self.request.query_params.get('q', None)
            if q:
                qs = (
                    Entry.objects.search(q)
                    .filter(owner=user)
                    .annotate(
                        type_source=KeyTextTransform('source', 'type'),
                        type_de=KeyTextTransform('de', KeyTextTransform('label', 'type')),
                        type_en=KeyTextTransform('en', KeyTextTransform('label', 'type')),
                    )
                )

            entry_pk = self.request.query_params.get('link_selection_for', None)
            if entry_pk:
                try:
                    entry = Entry.objects.get(pk=entry_pk, owner=user)
                    qs = qs.exclude(pk=entry_pk).exclude(to_entries__from_entry=entry)
                except Entry.DoesNotExist:
                    return Entry.objects.none()

        return qs


class RelationViewSet(viewsets.GenericViewSet, CreateModelMixin, DestroyModelMixin):
    """
    create:
    Create a new relation between entries.

    destroy:
    Delete a certain relation.
    """

    serializer_class = RelationSerializer

    def get_queryset(self):
        user = self.request.user
        return Relation.objects.filter(from_entry__owner=user, to_entry__owner=user)


class JsonSchemaViewSet(viewsets.ViewSet):
    """
    list:
    Returns a list of all available JSONSchemas.

    retrieve:
    Returns a certain JSONSchema.
    """

    lookup_value_regex = '.+'

    @language_header_decorator
    def list(self, request, *args, **kwargs):
        language = get_language() or 'en'
        return Response(sorted(ACTIVE_TYPES_LIST, key=lambda x: x.get('label', {}).get(language, '').lower()))

    @language_header_decorator
    def retrieve(self, request, pk=None, *args, **kwargs):
        schema = get_jsonschema(pk)
        if not schema:
            raise exceptions.NotFound(_('Schema not found for the given query.'))
        return Response(schema)


@swagger_auto_schema(methods=['get'], operation_id='api_v1_user_read')
@api_view(['GET'])
def user_information(request, *args, **kwargs):
    attributes = request.session.get('attributes', {})
    data = {
        'uuid': request.user.username,
        'name': attributes.get('display_name'),
        'email': attributes.get('email'),
        'permissions': attributes.get('permissions') or [],
        'groups': attributes.get('groups') or [],
        'space': get_free_space_for_user(request.user) if request.user else None,
    }

    return Response(data)


@swagger_auto_schema(
    methods=['get'],
    operation_id='api_v1_user_data',
    responses={
        200: openapi.Response(''),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('User not found'),
    },
    manual_parameters=[authorization_header_paramter, language_header_parameter],
)
@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((permissions.IsAuthenticated,))
def user_data(request, pk=None, *args, **kwargs):
    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(username=pk)
    except UserModel.DoesNotExist:
        raise exceptions.NotFound(_('User does not exist'))

    lang = get_language() or 'en'

    def entry_to_data(entry):
        return {
            'id': entry.pk,
            'title': entry.title,
            'subtitle': entry.subtitle or None,
            'type': entry.type.get('label').get(lang),
            'role': entry.owner_role_display,
            'location': entry.location_display,
            'year': entry.year_display,
        }

    def to_data_dict(label, data, sort=True):
        if sort:
            data = sorted(data, key=lambda x: x.get('year') or '0000', reverse=True) if data else []
        return {
            'label': label,
            'data': data,
        }

    published_entries_query = Entry.objects.filter(owner=user, published=True, type__isnull=False,).filter(
        Q(data__contains={'architecture': [{'source': user.username}]})
        | Q(data__contains={'authors': [{'source': user.username}]})
        | Q(data__contains={'artists': [{'source': user.username}]})
        | Q(data__contains={'winners': [{'source': user.username}]})
        | Q(data__contains={'granted_by': [{'source': user.username}]})
        | Q(data__contains={'jury': [{'source': user.username}]})
        | Q(data__contains={'music': [{'source': user.username}]})
        | Q(data__contains={'conductors': [{'source': user.username}]})
        | Q(data__contains={'composition': [{'source': user.username}]})
        | Q(data__contains={'organisers': [{'source': user.username}]})
        | Q(data__contains={'lecturers': [{'source': user.username}]})
        | Q(data__contains={'design': [{'source': user.username}]})
        | Q(data__contains={'commissions': [{'source': user.username}]})
        | Q(data__contains={'editors': [{'source': user.username}]})
        | Q(data__contains={'publishers': [{'source': user.username}]})
        | Q(data__contains={'curators': [{'source': user.username}]})
        | Q(data__contains={'fellow_scholar': [{'source': user.username}]})
        | Q(data__contains={'funding': [{'source': user.username}]})
        | Q(data__contains={'organisations': [{'source': user.username}]})
        | Q(data__contains={'project_lead': [{'source': user.username}]})
        | Q(data__contains={'project_partnership': [{'source': user.username}]})
        | Q(data__contains={'software_developers': [{'source': user.username}]})
        | Q(data__contains={'directors': [{'source': user.username}]})
        | Q(data__contains={'contributors': [{'source': user.username}]})
    )

    cache_key = f'user_data__{pk}_{lang}'

    cache_time, entries_count, usr_data = cache.get(cache_key, (None, None, None))

    if cache_time:
        last_modified = published_entries_query.aggregate(Max('date_changed'))['date_changed__max']
        if last_modified and last_modified < cache_time and entries_count == published_entries_query.count():
            return Response(usr_data)

    title_key = 'title'
    subtitle_key = 'subtitle'
    type_key = 'type'
    role_key = 'role'
    location_key = 'location'
    year_key = 'year'

    usr_data = {
        'entry_labels': {
            title_key: get_preflabel('title'),
            subtitle_key: get_preflabel('subtitle'),
            type_key: get_preflabel('type'),
            role_key: get_preflabel('role'),
            location_key: get_preflabel('location'),
            year_key: get_preflabel('year'),
        },
        'data': [],
    }

    document_schema = DocumentSchema()
    conference_schema = ConferenceSchema()
    event_schema = EventSchema()
    publications_label = get_altlabel_collection('collection_document_publication', lang=lang)
    monographs_label = get_altlabel_collection('collection_monograph', lang=lang)
    monographs_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_monograph')
    monographs_data = []
    composite_volumes_label = get_altlabel_collection('collection_composite_volume', lang=lang)
    composite_volumes_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_composite_volume'
    )
    composite_volumes_data = []
    articles_label = get_altlabel_collection('collection_article', lang=lang)
    articles_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_article')
    articles_data = []
    chapters_label = get_altlabel_collection('collection_chapter', lang=lang)
    chapters_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_chapter')
    chapters_data = []
    reviews_label = get_altlabel_collection('collection_review', lang=lang)
    reviews_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_review')
    reviews_data = []
    general_documents_publications_label = get_altlabel_collection(
        'collection_general_document_publication', lang=lang
    )
    general_documents_publications_data = []
    research_projects_label = get_altlabel_collection('collection_research_project', lang=lang)
    research_projects_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project'
    )
    research_projects_data = []
    awards_and_grants_label = get_altlabel_collection('collection_awards_and_grants', lang=lang)
    awards_and_grants_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_awards_and_grants'
    )
    awards_and_grants_data = []
    fellowships_visiting_affiliations_label = get_altlabel_collection(
        'collection_fellowship_visiting_affiliation',
        lang=lang,
    )
    fellowships_visiting_affiliations_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_fellowship_visiting_affiliation'
    )
    fellowships_visiting_affiliations_data = []
    exhibitions_label = get_altlabel_collection('collection_exhibition', lang=lang)
    exhibitions_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_exhibition')
    exhibitions_data = []
    supervisions_of_theses_label = get_altlabel_collection('collection_supervision_of_theses', lang=lang)
    supervisions_of_theses_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_supervision_of_theses'
    )
    supervisions_of_theses_data = []
    teaching_label = get_altlabel_collection('collection_teaching', lang=lang)
    teaching_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_teaching')
    teaching_data = []
    education_qualifications_label = get_altlabel_collection('collection_education_qualification', lang=lang)
    education_qualifications_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_education_qualification'
    )
    education_qualifications_data = []
    conferences_symposiums_label = get_altlabel_collection('collection_conference_symposium', lang=lang)
    conferences_symposiums_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference'
    )
    conferences_symposiums_data = []
    conference_contributions_label = get_altlabel_collection('collection_conference_contribution', lang=lang)
    conference_contributions_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_contribution'
    )
    conference_contributions_data = []
    architectures_label = get_altlabel_collection('collection_architecture', lang=lang)
    architectures_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_architecture')
    architectures_data = []
    audios_label = get_altlabel_collection('collection_audio', lang=lang)
    audios_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_audio')
    audios_data = []
    concerts_label = get_altlabel_collection('collection_concert', lang=lang)
    concerts_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_concert')
    concerts_data = []
    design_label = get_altlabel_collection('collection_design', lang=lang)
    design_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_design')
    design_data = []
    events_label = get_altlabel_collection('collection_event', lang=lang)
    events_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event')
    visual_and_verbal_presentations_label = get_altlabel_collection('collection_visual_verbal_presentation', lang=lang)
    visual_and_verbal_presentations_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_visual_verbal_presentation'
    )
    visual_and_verbal_presentations_data = []
    memberships_label = get_altlabel_collection('collection_membership ', lang=lang)
    memberships_data = []
    expert_functions_label = get_altlabel_collection('collection_expert_function ', lang=lang)
    expert_functions_data = []
    general_activities_label = get_altlabel_collection('collection_general_activity ', lang=lang)
    general_activities_data = []
    festivals_label = get_altlabel_collection('collection_festival', lang=lang)
    festivals_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_festival')
    festivals_data = []
    images_label = get_altlabel_collection('collection_image', lang=lang)
    images_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_image')
    images_data = []
    performances_label = get_altlabel_collection('collection_performance', lang=lang)
    performances_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_performance')
    performances_data = []
    sculptures_label = get_altlabel_collection('collection_sculpture', lang=lang)
    sculptures_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_sculpture')
    sculptures_data = []
    software_label = get_altlabel_collection('collection_software', lang=lang)
    software_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_software')
    software_data = []
    videos_label = get_altlabel_collection('collection_film_video', lang=lang)
    videos_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_film_video')
    videos_data = []
    general_publications_label = 'Sonstige Veröffentlichungen' if lang == 'de' else 'General Publications'
    general_publications_data = []

    published_entries = published_entries_query.order_by('title')

    for e in published_entries:
        entry_type = e.type.get('source')
        # Publications
        if entry_type in DOCUMENT_TYPES:
            e_data = document_schema.load(e.data).data
            # Monographs
            if (
                entry_type in monographs_types
                and e_data.authors is not None
                and any(i.source == user.username for i in e_data.authors)
            ):
                monographs_data.append(entry_to_data(e))
            # Composite Volumes
            elif (
                entry_type in composite_volumes_types
                and e_data.editors is not None
                and any(i.source == user.username for i in e_data.editors)
            ):
                composite_volumes_data.append(entry_to_data(e))
            # Articles
            elif (
                entry_type in articles_types
                and e_data.authors is not None
                and any(i.source == user.username for i in e_data.authors)
            ):
                articles_data.append(entry_to_data(e))
            # Chapters
            elif (
                entry_type in chapters_types
                and e_data.authors is not None
                and any(i.source == user.username for i in e_data.authors)
            ):
                chapters_data.append(entry_to_data(e))
            # Reviews
            elif (
                entry_type in reviews_types
                and e_data.authors is not None
                and any(i.source == user.username for i in e_data.authors)
            ):
                reviews_data.append(entry_to_data(e))
            # Supervisions of theses
            elif (
                entry_type in supervisions_of_theses_types
                and e_data.contributors is not None
                and any(
                    i.source == user.username
                    and i.roles is not None
                    and any(r.source == 'http://base.uni-ak.ac.at/portfolio/vocabulary/expertizing' for r in i.roles)
                    for i in e_data.contributors
                )
            ):
                supervisions_of_theses_data.append(entry_to_data(e))
            # General Documents/Publications
            else:
                general_documents_publications_data.append(entry_to_data(e))
        elif entry_type in conferences_symposiums_types:
            e_data = conference_schema.load(e.data).data
            # Teaching
            if (
                entry_type in teaching_types + education_qualifications_types
                and e_data.lecturers is not None
                and any(i.source == user.username for i in e_data.lecturers)
            ):
                teaching_data.append(entry_to_data(e))
            # Education & Qualifications
            elif (
                entry_type in education_qualifications_types
                and e_data.contributors is not None
                and any(
                    i.source == user.username
                    and i.roles is not None
                    and any(r.source == 'http://base.uni-ak.ac.at/portfolio/vocabulary/attendance' for r in i.roles)
                    for i in e_data.contributors
                )
            ):
                education_qualifications_data.append(entry_to_data(e))
            # Conferences & Symposiums
            else:
                conferences_symposiums_data.append(entry_to_data(e))
        elif entry_type in events_types:
            e_data = event_schema.load(e.data).data
            # Visual and verbal presentations
            if entry_type in visual_and_verbal_presentations_types:
                visual_and_verbal_presentations_data.append(entry_to_data(e))
            # Memberships
            elif e_data.contributors is not None and any(
                i.source == user.username
                and i.roles is not None
                and any(
                    r.source == 'http://base.uni-ak.ac.at/portfolio/vocabulary/member'
                    or r.source == 'http://base.uni-ak.ac.at/portfolio/vocabulary/board_member'
                    or r.source == 'http://base.uni-ak.ac.at/portfolio/vocabulary/advisory_board'
                    for r in i.roles
                )
                for i in e_data.contributors
            ):
                memberships_data.append(entry_to_data(e))
            # Expert Functions
            elif e_data.contributors is not None and any(
                i.source == user.username
                and i.roles is not None
                and any(r.source == 'http://base.uni-ak.ac.at/portfolio/vocabulary/expertizing' for r in i.roles)
                for i in e_data.contributors
            ):
                expert_functions_data.append(entry_to_data(e))
            # General Activities
            else:
                general_activities_data.append(entry_to_data(e))
        # Research Projects
        elif entry_type in research_projects_types:
            research_projects_data.append(entry_to_data(e))
        # Awards and Grants
        elif entry_type in awards_and_grants_types:
            awards_and_grants_data.append(entry_to_data(e))
        # Fellowships and visiting affiliations
        elif entry_type in fellowships_visiting_affiliations_types:
            fellowships_visiting_affiliations_data.append(entry_to_data(e))
        # Exhibitions
        elif entry_type in exhibitions_types:
            exhibitions_data.append(entry_to_data(e))
        # Conference contributons
        elif entry_type in conference_contributions_types:
            conference_contributions_data.append(entry_to_data(e))
        # Architectures
        elif entry_type in architectures_types:
            architectures_data.append(entry_to_data(e))
        # Audios
        elif entry_type in audios_types:
            audios_data.append(entry_to_data(e))
        # Concerts
        elif entry_type in concerts_types:
            concerts_data.append(entry_to_data(e))
        # Design
        elif entry_type in design_types:
            design_data.append(entry_to_data(e))
        # Festivals
        elif entry_type in festivals_types:
            festivals_data.append(entry_to_data(e))
        # Images
        elif entry_type in images_types:
            images_data.append(entry_to_data(e))
        # Performances
        elif entry_type in performances_types:
            performances_data.append(entry_to_data(e))
        # Sculptures
        elif entry_type in sculptures_types:
            sculptures_data.append(entry_to_data(e))
        # Software
        elif entry_type in software_types:
            software_data.append(entry_to_data(e))
        # Films/Videos
        elif entry_type in videos_types:
            videos_data.append(entry_to_data(e))
        # General Publications
        else:
            general_publications_data.append(e)

    # Publications
    publications_data = []

    for lbl, d in [
        (monographs_label, monographs_data),
        (composite_volumes_label, composite_volumes_data),
        (articles_label, articles_data),
        (chapters_label, chapters_data),
        (reviews_label, reviews_data),
        (general_documents_publications_label, general_documents_publications_data),
    ]:
        if d:
            publications_data.append(to_data_dict(lbl, d))

    # Teaching
    teaching_collected_data = []

    for lbl, d in [
        (supervisions_of_theses_label, supervisions_of_theses_data),
        (teaching_label, teaching_data),
    ]:
        if d:
            teaching_collected_data.append(to_data_dict(lbl, d))

    # Activities
    activities_data = []

    for lbl, d in [
        (memberships_label, memberships_data),
        (expert_functions_label, expert_functions_data),
        (visual_and_verbal_presentations_label, visual_and_verbal_presentations_data),
        (general_activities_label, general_activities_data),
    ]:
        if d:
            activities_data.append(to_data_dict(lbl, d))

    # Create return data in desired order
    for lbl, d, sort in (
        (publications_label, publications_data, False),
        (research_projects_label, research_projects_data, True),
        (awards_and_grants_label, awards_and_grants_data, True),
        (fellowships_visiting_affiliations_label, fellowships_visiting_affiliations_data, True),
        (exhibitions_label, exhibitions_data, True),
        (teaching_label, teaching_collected_data, False),
        (conferences_symposiums_label, conferences_symposiums_data, True),
        (conference_contributions_label, conference_contributions_data, True),
        (architectures_label, architectures_data, True),
        (audios_label, audios_data, True),
        (concerts_label, concerts_data, True),
        (design_label, design_data, True),
        (education_qualifications_label, education_qualifications_data, True),
        (events_label, activities_data, False),
        (festivals_label, festivals_data, True),
        (images_label, images_data, True),
        (performances_label, performances_data, True),
        (sculptures_label, sculptures_data, True),
        (software_label, software_data, True),
        (videos_label, videos_data, True),
        (general_publications_label, general_publications_data, True),
    ):
        if d:
            usr_data['data'].append(to_data_dict(lbl, d, sort=sort))

    usr_data = usr_data if usr_data['data'] else {'data': []}

    entries_count = published_entries_query.count()

    cache.set(cache_key, (timezone.now(), entries_count, usr_data), 86400)

    return Response(usr_data)


def get_media_for_entry_public(entry):
    lang = get_language() or 'en'
    media = get_media_for_entry(entry, flat=False, published=True)
    for m in media:
        try:
            del m['metadata']
        except KeyError:
            pass
        if m.get('license'):
            m['license'] = m.get('license', {}).get('label', {}).get(lang)
    return media


@swagger_auto_schema(
    methods=['get'],
    operation_id='api_v1_user_entry_data',
    responses={
        200: openapi.Response(''),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('User or entry not found'),
    },
    manual_parameters=[authorization_header_paramter, language_header_parameter],
)
@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((permissions.IsAuthenticated,))
def user_entry_data(request, pk=None, entry=None, *args, **kwargs):
    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(username=pk)
    except UserModel.DoesNotExist:
        raise exceptions.NotFound(_('User does not exist'))

    try:
        e = Entry.objects.get(pk=entry, owner=user, published=True)
    except Entry.DoesNotExist:
        raise exceptions.NotFound(_('Entry does not exist'))

    ret = e.data_display
    ret['media'] = get_media_for_entry_public(entry)

    return Response(ret)


@swagger_auto_schema(
    methods=['get'],
    operation_id='api_v1_entry_data',
    responses={
        200: openapi.Response(''),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('Entry not found'),
    },
    manual_parameters=[authorization_header_paramter, language_header_parameter],
)
@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((permissions.IsAuthenticated,))
def entry_data(request, pk=None, *args, **kwargs):
    try:
        e = Entry.objects.get(pk=pk, published=True)
    except Entry.DoesNotExist:
        raise exceptions.NotFound(_('Entry does not exist'))

    ret = e.data_display
    ret['media'] = get_media_for_entry_public(pk)

    return Response(ret)


@swagger_auto_schema(
    methods=['post'],
    operation_id='api_v1_wb_data',
    responses={
        200: openapi.Response(''),
        400: openapi.Response('Bad Request'),
        403: openapi.Response('Access not allowed'),
    },
    manual_parameters=[
        authorization_header_paramter,
        language_header_parameter,
        openapi.Parameter('collection', openapi.IN_FORM, required=True, type=openapi.TYPE_STRING),
        openapi.Parameter('roles', openapi.IN_FORM, required=True, type=openapi.TYPE_STRING),
        openapi.Parameter('users', openapi.IN_FORM, required=True, type=openapi.TYPE_STRING),
    ],
)
@api_view(['POST'])
@parser_classes([FormParser, MultiPartParser])
@authentication_classes((TokenAuthentication,))
@permission_classes((permissions.IsAuthenticated,))
def wb_data(request, *args, **kwargs):
    users = request.POST.getlist('users') or []
    types = (
        (get_collection_members(request.POST.get('types')) or request.POST.get('types').split(','))
        if request.POST.get('types')
        else None
    )
    roles = request.POST.getlist('roles') or []
    year = request.POST.get('year') or None

    if not users or not types or not roles or not year:
        raise exceptions.ParseError()

    date_filters = []
    q_filters = []

    schemas = []

    for t in types:
        schemas.append(get_schema(t))

    date_fields = []

    for s in list(set(schemas)):
        date_fields += s().date_fields

    for df in list(set(date_fields)):
        date_filters.append({f'data__{df}__icontains': year})

    for user in users:
        for role in roles:
            q_filters.append(dict(data__contains={role: [{'source': user}]}))

    qs = (
        Entry.objects.filter(
            published=True,
            type__source__in=types,
        )
        .filter(reduce(operator.or_, (Q(**x) for x in date_filters)))
        .filter(reduce(operator.or_, (Q(**x) for x in q_filters)))
        .annotate(rel=ArrayAgg('relations__id'))
        .values(
            'id',
            'date_created',
            'date_changed',
            'owner__username',
            'title',
            'subtitle',
            'type',
            'reference',
            'keywords',
            'texts',
            'data',
            'rel',
        )
    )

    return Response(qs)
