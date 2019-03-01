from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework import exceptions, filters, viewsets, permissions
from rest_framework.decorators import action, api_view
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from core.models import Entity, Relation
from core.schemas import ACTIVE_TYPES, get_jsonschema
from media_server.models import get_media_for_entity
from media_server.utils import get_free_space_for_user
from .serializers.entity import EntitySerializer
from .serializers.relation import RelationSerializer
from .yasg import JSONAutoSchema, UserOperationIDAutoSchema

schema_view = get_schema_view(
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

no_ui_view = schema_view.without_ui(cache_timeout=0)
swagger_view = schema_view.with_ui('swagger', cache_timeout=0)
redoc_view = schema_view.with_ui('redoc', cache_timeout=0)


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


@method_decorator(name='list', decorator=swagger_auto_schema(
    manual_parameters=[
        openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING),
        openapi.Parameter(
            'link_selection_for',
            openapi.IN_QUERY,
            description="Get link selection for a certain entity",
            type=openapi.TYPE_STRING
        ),
    ]
))
class EntityViewSet(viewsets.ModelViewSet, CountModelMixin):
    """
    retrieve:
    Returns a certain entity.

    list:
    Returns a list of all entities for current user.

    create:
    Create a new instance of entity for current user.

    update:
    Update a certain entity.

    partial_update:
    Partially update a certain entity.

    destroy:
    Delete a certain entity.

    count:
    Returns the number of documents of type entity.

    media:
    Return list of media objects.
    """

    serializer_class = EntitySerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('type',)  # TODO
    ordering_fields = ('title', 'date_created', 'date_changed', 'published', 'type')  # TODO
    pagination_class = StandardLimitOffsetPagination
    swagger_schema = JSONAutoSchema

    @swagger_auto_schema(responses={
        200: openapi.Response(''),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('Entity not found'),
    })
    @action(detail=True)
    def media(self, request, pk=None, *args, **kwargs):
        try:
            entity = Entity.objects.get(pk=pk)
            if entity.owner != request.user:
                raise exceptions.PermissionDenied(_('Current user is not the owner of this entity'))
            ret = get_media_for_entity(entity.pk)
            return Response(ret)
        except Entity.DoesNotExist:
            raise exceptions.NotFound(_('Entity does not exist'))

    @swagger_auto_schema(responses={200: openapi.Response('')})
    @action(detail=False, filter_backends=[], pagination_class=None)
    def types(self, request, *args, **kwargs):
        content = self.get_queryset().exclude(
            type__isnull=True).exclude(type__exact='').values_list('type', flat=True).distinct().order_by()
        return Response(content)

    def get_queryset(self):
        user = self.request.user
        qs = Entity.objects.filter(owner=user).order_by('-date_changed')

        if self.action == 'list':
            q = self.request.query_params.get('q', None)
            if q:
                qs = Entity.objects.search(q).filter(owner=user)

            entity_pk = self.request.query_params.get('link_selection_for', None)
            if entity_pk:
                try:
                    entity = Entity.objects.get(pk=entity_pk, owner=user)
                    qs = qs.exclude(pk=entity_pk).exclude(to_entities__from_entity=entity)
                except Entity.DoesNotExist:
                    return Entity.objects.none()

        return qs


class RelationViewSet(viewsets.GenericViewSet, CreateModelMixin, DestroyModelMixin):
    """
    create:
    Create a new relation between entities.

    destroy:
    Delete a certain relation.
    """

    serializer_class = RelationSerializer

    def get_queryset(self):
        user = self.request.user
        return Relation.objects.filter(from_entity__owner=user, to_entity__owner=user)


class JsonSchemaViewSet(viewsets.ViewSet):
    """
    list:
    Returns a list of all available JSONSchemas.

    retrieve:
    Returns a certain JSONSchema.
    """

    def list(self, request, *args, **kwargs):
        return Response(ACTIVE_TYPES)

    def retrieve(self, request, pk=None, *args, **kwargs):
        schema = get_jsonschema(pk)
        if not schema:
            raise exceptions.NotFound(_('Schema not found for the given query.'))
        return Response(schema)


@swagger_auto_schema(methods=['get'], auto_schema=UserOperationIDAutoSchema)
@api_view(['GET'])
def user_information(request, *args, **kwargs):
    attributes = request.session.get('attributes', {})
    data = {
        'name': attributes.get('display_name'),
        'email': attributes.get('email'),
        'permissions': attributes.get('permissions').split(',') if attributes.get('permissions') else [],
        'groups': attributes.get('groups').split(',') if attributes.get('groups') else [],
        'space': get_free_space_for_user(request.user) if request.user else None,
    }

    return Response(data)
