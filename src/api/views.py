from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _, get_language
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from drf_yasg import openapi
from drf_yasg.codecs import OpenAPICodecJson
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework import exceptions, filters, viewsets, permissions
from rest_framework.decorators import action, api_view
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from core.models import Entry, Relation
from core.schemas import ACTIVE_TYPES_LIST, get_jsonschema
from media_server.models import get_media_for_entry
from media_server.utils import get_free_space_for_user
from .serializers.entry import EntrySerializer
from .serializers.relation import RelationSerializer
from .yasg import JSONAutoSchema, OpenAPICodecDRFJson, language_header_decorator

SchemaView = get_schema_view(
    openapi.Info(
        title="Portfolio API",
        default_version=settings.REST_FRAMEWORK.get('DEFAULT_VERSION'),
        # description="",
        # terms_of_service="",
        # contact=openapi.Contact(email=""),
        # license=openapi.License(name=""),
    ),
    validators=['flex', 'ssv'] if settings.DEBUG else None,
    public=False,
    # permission_classes=(permissions.IsAuthenticated,),
)


class PortfolioSchemaView(SchemaView):
    def __init__(self, **kwargs):
        super(PortfolioSchemaView, self).__init__(**kwargs)
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


class CountModelMixin(object):
    """
    Count a queryset.
    """
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


entry_ordering_fields = ('title', 'date_created', 'date_changed', 'published', 'type_source')


@method_decorator(swagger_auto_schema(
    manual_parameters=[
        openapi.Parameter(
            'sort',
            openapi.IN_QUERY,
            required=False,
            description='Which field to use when ordering the results.',
            type=openapi.TYPE_STRING,
            enum=list(entry_ordering_fields) + ['-{}'.format(i) for i in entry_ordering_fields],
        ),
        openapi.Parameter('q', openapi.IN_QUERY, required=False, description='Search query', type=openapi.TYPE_STRING),
        openapi.Parameter(
            'link_selection_for',
            openapi.IN_QUERY,
            required=False,
            description='Get link selection for a certain entry',
            type=openapi.TYPE_STRING
        ),
    ]
), name='list')
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
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filterset_class = EntryFilter
    ordering_fields = entry_ordering_fields
    pagination_class = StandardLimitOffsetPagination
    swagger_schema = JSONAutoSchema

    @swagger_auto_schema(responses={
        200: openapi.Response(''),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('Entry not found'),
    })
    @action(detail=True, filter_backends=[], pagination_class=None)
    def media(self, request, pk=None, *args, **kwargs):
        try:
            entry = Entry.objects.get(pk=pk)
            if entry.owner != request.user:
                raise exceptions.PermissionDenied(_('Current user is not the owner of this entry'))
            ret = get_media_for_entry(entry.pk)
            return Response(ret)
        except Entry.DoesNotExist:
            raise exceptions.NotFound(_('Entry does not exist'))

    @swagger_auto_schema(responses={200: openapi.Response('')})
    @action(detail=False, filter_backends=[], pagination_class=None)
    def types(self, request, *args, **kwargs):
        language = get_language() or 'en'
        content = self.get_queryset().exclude(
            type__isnull=True).exclude(type__exact='').values_list('type', flat=True).distinct().order_by()
        return Response(sorted(content, key=lambda x: x.get('label', {}).get(language, '').lower()))

    def get_queryset(self):
        user = self.request.user
        qs = Entry.objects.filter(owner=user).annotate(
            type_source=KeyTextTransform('source', 'type')
        ).order_by('-date_changed')

        if self.action == 'list':
            q = self.request.query_params.get('q', None)
            if q:
                qs = Entry.objects.search(q).filter(owner=user)

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


@method_decorator(language_header_decorator, name='retrieve')
class JsonSchemaViewSet(viewsets.ViewSet):
    """
    list:
    Returns a list of all available JSONSchemas.

    retrieve:
    Returns a certain JSONSchema.
    """
    lookup_value_regex = '.+'

    def list(self, request, *args, **kwargs):
        language = get_language() or 'en'
        return Response(sorted(ACTIVE_TYPES_LIST, key=lambda x: x.get('label', {}).get(language, '').lower()))

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
