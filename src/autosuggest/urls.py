from django.conf.urls import url

from . import views

# NOTE: fieldname must be present in ACTIVE_SOURCES in portfolio/settings for this to work
urlpatterns = [
    url(r'^(?P<fieldname>(\w+))/$', views.lookup_view, name='lookup_all'),
    url(r'^(?P<fieldname>(\w+))/(?P<searchstr>(.+))/$', views.lookup_view_search, name='lookup'),
]
