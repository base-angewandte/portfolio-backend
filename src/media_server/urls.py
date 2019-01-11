from django.conf import settings
from django.conf.urls import url

from .views import protected_view

urlpatterns = [
    url(r'^(?P<path>.*)$', protected_view, {'server': settings.PROTECTED_MEDIA_SERVER, }, name='protected_media'),
]
