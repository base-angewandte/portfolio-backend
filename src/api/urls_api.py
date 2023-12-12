from rest_framework import routers

from django.urls import include, path, re_path

from media_server.views import MediaViewSet

from . import views

router = routers.DefaultRouter()
router.register(r'entry', views.EntryViewSet, basename='entry')
router.register(r'relation', views.RelationViewSet, basename='relation')
router.register(r'jsonschema', views.JsonSchemaViewSet, basename='jsonschema')
router.register(r'media', MediaViewSet, basename='media')


urlpatterns = [
    path('', include(router.urls)),
    path('user/', views.user_information, name='user'),
    path('user/<str:pk>/data/', views.user_data, name='user_data'),
    path(
        'user/<str:pk>/data/<str:entry>/',
        views.user_entry_data,
        name='user_entry_data',
    ),
    path('entry/<str:pk>/data/', views.entry_data, name='entry_data'),
    path('wbdata/', views.wb_data, name='wb_data'),
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        views.no_ui_view,
        name='schema-json',
    ),
    path('swagger/', views.swagger_view, name='schema-swagger-ui'),
    path('redoc/', views.redoc_view, name='schema-redoc'),
]
