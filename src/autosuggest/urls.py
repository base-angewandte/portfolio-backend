from . import views
from django.conf.urls import url

from rest_framework import routers
# from django.urls import path

urlpatterns = [url(r'(?P<fieldname>(.+))/(?P<searchstr>(.+))/$',
                   views.lookup_view, name='lookup')]
