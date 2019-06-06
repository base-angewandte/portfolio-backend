from django.conf.urls import include, url
from rest_framework import routers

from media_server.views import MediaViewSet
from . import views


router = routers.DefaultRouter()
router.register(r'entry', views.EntryViewSet, basename='entry')
router.register(r'relation', views.RelationViewSet, basename='relation')
router.register(r'jsonschema', views.JsonSchemaViewSet, basename='jsonschema')
router.register(r'media', MediaViewSet, basename='media')


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'user/$', views.user_information, name='user'),

    url(r'^swagger(?P<format>\.json|\.yaml)$', views.no_ui_view, name='schema-json'),
    url(r'^swagger/$', views.swagger_view, name='schema-swagger-ui'),
    url(r'^redoc/$', views.redoc_view, name='schema-redoc'),
]
