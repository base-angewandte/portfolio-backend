from django.conf.urls import include, url
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'entity', views.EntityViewSet)
router.register(r'relation', views.RelationViewSet)
router.register(r'jsonschema', views.JsonSchemaViewSet, base_name='jsonschema')


urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^swagger(?P<format>\.json|\.yaml)$', views.no_ui_view, name='schema-json'),
    url(r'^swagger/$', views.swagger_view, name='schema-swagger-ui'),
    url(r'^redoc/$', views.redoc_view, name='schema-redoc'),
]
