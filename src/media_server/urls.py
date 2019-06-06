from django.conf import settings
from django.urls import re_path

from .views import protected_view

urlpatterns = [
    re_path(r'^(?P<path>.*)$', protected_view, {'server': settings.PROTECTED_MEDIA_SERVER, }, name='protected_media'),
]
