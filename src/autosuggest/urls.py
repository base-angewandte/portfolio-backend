from . import views
from django.conf.urls import include, url
from rest_framework import routers
from django.urls import path

urlpatterns = [
    path(r'person/<searchstr>/', views.lookup_person_view),
    path(r'place/<searchstr>/', views.lookup_place_view, name='place'),
]
