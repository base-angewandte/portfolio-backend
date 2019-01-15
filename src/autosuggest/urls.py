from . import views
from django.conf.urls import include, url
from rest_framework import routers
from django.urls import path

#router = routers.SimpleRouter()
#vrouter.register(r'person', views.PersonViewSet, base_name='person')

urlpatterns = [
    url('person/', views.lookup_person_view, name='person'),
    url('place/', views.lookup_place_view, name='place'),
]
