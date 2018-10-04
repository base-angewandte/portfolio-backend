from django.conf.urls import include, url

from . import urls_api


urlpatterns = [
    url(r'^(?P<version>(v1))/', include(urls_api)),
    # url(r'^auth/', include('rest_framework.urls')),
]
