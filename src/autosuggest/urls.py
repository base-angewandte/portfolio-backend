from django.conf import settings
from django.conf.urls import url

from . import views

# NOTE: fieldname must be present in ACTIVE_SOURCES in portfolio/settings for this to work
urlpatterns = [
    url(
        r'^(?P<fieldname>({}))/$'.format('|'.join(settings.ACTIVE_SOURCES.keys())),
        views.lookup_view,
        name='lookup_all',
    ),
    url(
        r'^(?P<fieldname>({}))/(?P<searchstr>(.+))/$'.format('|'.join(settings.ACTIVE_SOURCES.keys())),
        views.lookup_view_search,
        name='lookup',
    ),
]
