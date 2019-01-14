from django.conf import settings
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework import filters, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from core.models import Entity, Relation
from core.schemas import ACTIVE_TYPES, get_jsonschema
from media_server.models import get_media_for_parent
from .serializers import EntitySerializer, RelationSerializer
from .yasg import JSONAutoSchema

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
    ordering_fields = ('title',)  # TODO
    pagination_class = StandardLimitOffsetPagination
    swagger_schema = JSONAutoSchema

    @action(detail=True)
    def media(self, request, pk=None, *args, **kwargs):
        ret = get_media_for_parent(request, pk)
        return Response(ret)

    def get_queryset(self):
        user = self.request.user
        return Entity.objects.filter(owner=user).order_by('-date_changed')


class RelationViewSet(viewsets.ModelViewSet, CountModelMixin):
    """
    retrieve:
    Returns a certain relation.

    list:
    Returns a list of all relations for current user.

    create:
    Create a new relation between entities.

    update:
    Update a certain relation.

    partial_update:
    Partially update a certain relation.

    destroy:
    Delete a certain relation.

    count:
    Returns the number of documents of type relation.
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
            raise Http404(_('Schema not found for the given query.'))
        return Response(schema)
