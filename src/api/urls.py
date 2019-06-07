from django.urls import include, re_path

from . import urls_api


urlpatterns = [
    re_path(r'^(?P<version>(v1))/', include(urls_api)),
    # path('auth/', include('rest_framework.urls')),
]
