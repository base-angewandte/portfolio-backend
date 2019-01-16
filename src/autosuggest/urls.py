from . import views
from django.conf.urls import url

from rest_framework import routers
# from django.urls import path

urlpatterns = [
    url(r'person/(?P<searchstr>(.+))/$', views.lookup_person_view, name='person'),
    url(r'person/$', views.lookup_person_view, name='person'),
    url(r'place/(?P<searchstr>(.+))/$', views.lookup_place_view, name='place'),
    url(r'place/$', views.lookup_place_view, name='place'),
]
