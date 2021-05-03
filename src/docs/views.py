from django.conf import settings
from django.views.static import serve


def serve_docs(request, path, **kwargs):
    if not ('document_root' in kwargs or settings.DOCS_ROOT):
        raise ValueError('No document root defined')
    if 'document_root' not in kwargs:
        kwargs['document_root'] = settings.DOCS_ROOT
    return serve(request, path, **kwargs)
