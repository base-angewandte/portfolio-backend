import json
import logging
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
from core.schemas.entries.document import TYPES as DOCUMENT_TYPES
from core.skosmos import get_altlabel_collection, get_collection_members, get_preflabel
from general.drf.authentication import TokenAuthentication
from general.drf.filters import CaseInsensitiveOrderingFilter
from media_server.archiver import Archiver
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

    archive:
    Archive the media objects (e.g.in a Phaidra container).
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
        responses={
            200: openapi.Response(''),
            403: openapi.Response('Access not allowed'),
            404: openapi.Response('Entry not found'),
        },
    )
    @action(detail=True, filter_backends=[], pagination_class=None)
    def archive(self, request, pk=None, *args, **kwargs):
        try:
            entry = Entry.objects.get(pk=pk)
            if entry.owner != request.user:
                raise exceptions.PermissionDenied(_('Current user is not the owner of this entry'))
            if not settings.ARCHIVE_TYPE:
                # No archival configured, abort
                raise exceptions.PermissionDenied(_('No archival system configured.'))

            archiver = Archiver()
            res = archiver.archive(entry)


            return Response(res)
        except Entry.DoesNotExist:
            raise exceptions.NotFound(_('Entry does not exist'))


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

    cache_key = f'user_data__{pk}_{lang}'

    cache_time, entries_count, usr_data = cache.get(cache_key, (None, None, None))

    if cache_time:
        last_modified = Entry.objects.filter(owner=user, published=True).aggregate(Max('date_changed'))[
            'date_changed__max'
        ]
        if (
            last_modified
            and last_modified < cache_time
            and entries_count == Entry.objects.filter(owner=user, published=True).count()
        ):
            return Response(usr_data)

    def get_data(label, kw_filters, q_filters=None, exclude_filters=None):
        ret = {
            'label': label,
            'data': [],
        }
        ret_keys = []

        qs = Entry.objects.filter(owner=user, published=True, **kw_filters)

        if q_filters:
            qs = qs.filter(reduce(operator.or_, (Q(**x) for x in q_filters)))

        if exclude_filters:
            qs = qs.exclude(**exclude_filters)

        qs = qs.order_by('title')

        for e in qs:
            ret_keys.append(e.pk)
            ret['data'].append(
                {
                    'id': e.pk,
                    'title': e.title,
                    'subtitle': e.subtitle or None,
                    'type': e.type.get('label').get(lang),
                    'role': e.owner_role_display,
                    'location': e.location_display,
                    'year': e.year_display,
                }
            )

        ret['data'] = sorted(ret['data'], key=lambda x: x['year'] or '0000', reverse=True)

        return ret, ret_keys

    general_publications_q_filters = []

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

    exclude = []

    # Publications collected
    pub_data = {
        'label': get_altlabel_collection('collection_document_publication', lang=lang),
        'data': [],
    }

    monographs_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_monograph')
    composite_volumes_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_composite_volume'
    )
    articles_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_article')
    chapters_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_chapter')
    reviews_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_review')

    for lbl, f, qf in (
        # Monographs
        (
            get_altlabel_collection('collection_monograph', lang=lang),
            dict(
                type__source__in=monographs_types,
                data__contains={'authors': [{'source': user.username}]},
            ),
            None,
        ),
        # Composite Volumes
        (
            get_altlabel_collection('collection_composite_volume', lang=lang),
            dict(
                type__source__in=composite_volumes_types,
                data__contains={'editors': [{'source': user.username}]},
            ),
            None,
        ),
        # Articles
        (
            get_altlabel_collection('collection_article', lang=lang),
            dict(
                type__source__in=articles_types,
                data__contains={'authors': [{'source': user.username}]},
            ),
            None,
        ),
        # Chapters
        (
            get_altlabel_collection('collection_chapter', lang=lang),
            dict(
                type__source__in=chapters_types,
                data__contains={'authors': [{'source': user.username}]},
            ),
            None,
        ),
        # Reviews
        (
            get_altlabel_collection('collection_review', lang=lang),
            dict(
                type__source__in=reviews_types,
                data__contains={'authors': [{'source': user.username}]},
            ),
            None,
        ),
    ):
        if qf:
            general_publications_q_filters += qf
        d, k = get_data(lbl, f, qf)
        if d['data']:
            pub_data['data'].append(d)
        if k:
            exclude += k

    # General Documents/Publications
    lbl = '{} {}'.format(
        'Sonstige' if lang == 'de' else 'General',
        get_altlabel_collection('collection_document_publication', lang=lang),
    )
    f = dict(type__source__in=DOCUMENT_TYPES)
    qf = [
        dict(data__contains={'authors': [{'source': user.username}]}),
        dict(data__contains={'editors': [{'source': user.username}]}),
        dict(data__contains={'publishers': [{'source': user.username}]}),
        dict(data__contains={'contributors': [{'source': user.username}]}),
    ]
    e = dict(pk__in=exclude)
    general_publications_q_filters += qf
    d, k = get_data(lbl, f, qf, e)
    if d['data']:
        pub_data['data'].append(d)
    if k:
        exclude += k

    if pub_data['data']:
        usr_data['data'].append(pub_data)

    research_projects_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project'
    )
    awards_and_grants_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_awards_and_grants'
    )
    exhibitions_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_exhibition')
    teaching_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_teaching')
    educations_qualifications_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_education_qualification'
    )
    conferences_symposiums_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_symposium'
    )
    conference_contributions_types = get_collection_members(
        'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_contribution'
    )
    architectures_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_architecture')
    audios_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_audio')
    concerts_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_concert')
    events_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event')
    festivals_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_festival')
    images_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_image')
    performances_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_performance')
    sculptures_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_sculpture')
    softwares_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_software')
    videos_types = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_film_video')

    for lbl, f, qf in (
        # Research Projects
        (
            get_altlabel_collection('collection_research_project', lang=lang),
            dict(
                type__source__in=research_projects_types,
            ),
            [
                dict(data__contains={'project_lead': [{'source': user.username}]}),
                dict(data__contains={'project_partnership': [{'source': user.username}]}),
                dict(data__contains={'funding': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Awards and Grants
        (
            get_altlabel_collection('collection_awards_and_grants', lang=lang),
            dict(
                type__source__in=awards_and_grants_types,
            ),
            [
                dict(data__contains={'winners': [{'source': user.username}]}),
                dict(data__contains={'granted_by': [{'source': user.username}]}),
                dict(data__contains={'jury': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Exhibitions
        (
            get_altlabel_collection('collection_exhibition', lang=lang),
            dict(
                type__source__in=exhibitions_types,
            ),
            [
                dict(data__contains={'artists': [{'source': user.username}]}),
                dict(data__contains={'curators': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Teaching
        (
            get_altlabel_collection('collection_teaching', lang=lang),
            dict(
                type__source__in=teaching_types,
            ),
            [
                dict(data__contains={'organisers': [{'source': user.username}]}),
                dict(data__contains={'lecturers': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Educations & Qualifications
        (
            get_altlabel_collection('collection_education_qualification', lang=lang),
            dict(
                type__source__in=educations_qualifications_types,
            ),
            [
                dict(data__contains={'organisers': [{'source': user.username}]}),
                dict(data__contains={'lecturers': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Conferences & Symposiums
        (
            get_altlabel_collection('collection_conference_symposium', lang=lang),
            dict(
                type__source__in=conferences_symposiums_types,
            ),
            [
                dict(data__contains={'organisers': [{'source': user.username}]}),
                dict(data__contains={'lecturers': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Conference contributons
        (
            get_altlabel_collection('collection_conference_contribution', lang=lang),
            dict(
                type__source__in=conference_contributions_types,
            ),
            [
                dict(data__contains={'lecturers': [{'source': user.username}]}),
                dict(data__contains={'organisers': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Architectures
        (
            get_altlabel_collection('collection_architecture', lang=lang),
            dict(
                type__source__in=architectures_types,
            ),
            [
                dict(data__contains={'architecture': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Audios
        (
            get_altlabel_collection('collection_audio', lang=lang),
            dict(
                type__source__in=audios_types,
            ),
            [
                dict(data__contains={'authors': [{'source': user.username}]}),
                dict(data__contains={'artists': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Concerts
        (
            get_altlabel_collection('collection_concert', lang=lang),
            dict(
                type__source__in=concerts_types,
            ),
            [
                dict(data__contains={'music': [{'source': user.username}]}),
                dict(data__contains={'conductors': [{'source': user.username}]}),
                dict(data__contains={'composition': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Events
        (
            get_altlabel_collection('collection_event', lang=lang),
            dict(
                type__source__in=events_types,
            ),
            [dict(data__contains={'contributors': [{'source': user.username}]})],
        ),
        # Festivals
        (
            get_altlabel_collection('collection_festival', lang=lang),
            dict(
                type__source__in=festivals_types,
            ),
            [
                dict(data__contains={'organisers': [{'source': user.username}]}),
                dict(data__contains={'artists': [{'source': user.username}]}),
                dict(data__contains={'curators': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Images
        (
            get_altlabel_collection('collection_image', lang=lang),
            dict(
                type__source__in=images_types,
            ),
            [
                dict(data__contains={'artists': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Performances
        (
            get_altlabel_collection('collection_performance', lang=lang),
            dict(
                type__source__in=performances_types,
            ),
            [
                dict(data__contains={'artists': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Sculptures
        (
            get_altlabel_collection('collection_sculpture', lang=lang),
            dict(
                type__source__in=sculptures_types,
            ),
            [
                dict(data__contains={'artists': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Softwares
        (
            get_altlabel_collection('collection_software', lang=lang),
            dict(
                type__source__in=softwares_types,
            ),
            [
                dict(data__contains={'software_developers': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
        # Videos
        (
            get_altlabel_collection('collection_film_video', lang=lang),
            dict(
                type__source__in=videos_types,
            ),
            [
                dict(data__contains={'directors': [{'source': user.username}]}),
                dict(data__contains={'contributors': [{'source': user.username}]}),
            ],
        ),
    ):
        if qf:
            general_publications_q_filters += qf
        d, k = get_data(lbl, f, qf)
        if d['data']:
            usr_data['data'].append(d)
        if k:
            exclude += k

    # General Publications
    d, k = get_data(
        'Sonstige Veröffentlichungen' if lang == 'de' else 'General Publications',
        {},
        [json.loads(s) for s in {json.dumps(d, sort_keys=True) for d in general_publications_q_filters}],
        dict(pk__in=exclude),
    )
    if d['data']:
        usr_data['data'].append(d)

    usr_data = usr_data if usr_data['data'] else {'data': []}

    entries_count = Entry.objects.filter(owner=user, published=True).count()

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
