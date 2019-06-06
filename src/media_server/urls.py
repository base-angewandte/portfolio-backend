from django.conf import settings
from django.urls import path

from .views import protected_view

urlpatterns = [
    path('<path:path>', protected_view, {'server': settings.PROTECTED_MEDIA_SERVER, }, name='protected_media'),
]
