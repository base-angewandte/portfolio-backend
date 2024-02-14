from rest_framework import routers

from django.urls import include, path, re_path, reverse_lazy
from django.views.generic import RedirectView

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
    # redirects for compatibility with older versions
    path(
        'swagger.json',
        RedirectView.as_view(
            url=reverse_lazy('schema', kwargs={'version': 'v1', 'format': '.json'}),
            permanent=True,
        ),
    ),
    path(
        'swagger.yaml',
        RedirectView.as_view(
            url=reverse_lazy('schema', kwargs={'version': 'v1', 'format': '.yaml'}),
            permanent=True,
        ),
    ),
    path(
        'swagger/',
        RedirectView.as_view(
            url=reverse_lazy('schema-docs', kwargs={'version': 'v1'}),
            permanent=True,
        ),
    ),
    path(
        'redoc/',
        RedirectView.as_view(
            url=reverse_lazy('schema-docs', kwargs={'version': 'v1'}),
            permanent=True,
        ),
    ),
    # schema and schema docs
    re_path(
        r'^openapi(?P<format>\.json|\.yaml)$',
        views.no_ui_view,
        name='schema',
    ),
    path('docs/', views.swagger_view, name='schema-docs'),
]
