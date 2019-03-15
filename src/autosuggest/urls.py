from . import views
from django.conf.urls import url

from rest_framework import routers
# from django.urls import path

urlpatterns = [url(r'^(?P<fieldname>(\w+))/$', views.lookup_view, name='lookup_all'),
               url(r'^(?P<fieldname>(\w+))/(?P<searchstr>(.+))/$', views.lookup_view, name='lookup')]
