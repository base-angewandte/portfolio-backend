from django.urls import path, re_path

from .decorators import basicauth
from .views import serve_docs

docs_view = basicauth(serve_docs)

urlpatterns = [
    path('', docs_view, {'path': 'index.html'}),
    re_path(r'^(?P<path>.*)$', docs_view),
]
