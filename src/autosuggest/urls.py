from django.urls import include, re_path

from . import urls_autosuggest

urlpatterns = [
    re_path(r'^(?P<version>(v1))/', include(urls_autosuggest)),
]
