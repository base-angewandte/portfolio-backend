import logging
import mimetypes
from os.path import basename, join

import magic
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .decorators import is_allowed
from .models import PREFIX_TO_MODEL, get_model_for_mime_type
from .serializers import MediaSerializer

logger = logging.getLogger(__name__)


@login_required
@is_allowed
def protected_view(request, path, server, as_download=False):
    if server == 'nginx':
        mimetype, encoding = mimetypes.guess_type(path)

        response = HttpResponse()

        response['Content-Type'] = mimetype

        if encoding:
            response['Content-Encoding'] = encoding

        if as_download:
            response['Content-Disposition'] = "attachment; filename={}".format(basename(path))

        response['X-Accel-Redirect'] = join(settings.PROTECTED_MEDIA_LOCATION, path).encode('utf8')
        return response

    elif server == 'django':
        return serve(
            request,
            path,
            document_root=settings.PROTECTED_MEDIA_ROOT,
            show_indexes=False,
        )

    return HttpResponseServerError()


# DRF views

class MediaViewSet(viewsets.GenericViewSet):
    serializer_class = MediaSerializer
    parser_classes = (FormParser, MultiPartParser)

    @swagger_auto_schema(responses={
        200: openapi.Response(''),
        202: openapi.Response('Media object is still converting'),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('Media object not found'),
    })
    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            model = PREFIX_TO_MODEL.get(pk[0])
            if model:
                try:
                    m = model.objects.get(id=pk)

                    if m.owner != request.user:
                        return Response(
                            _('Current user is not the owner of this media object'),
                            status=status.HTTP_403_FORBIDDEN,
                        )
                    elif m.status != 2:
                        return Response(
                            {'id': pk},
                            status=status.HTTP_202_ACCEPTED
                        )

                    return Response(m.get_data())
                except model.DoesNotExist:
                    pass

        return Response(_('Media object does not exist'), status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        serializer = MediaSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():

            mime_type = magic.from_buffer(serializer.validated_data['file'].read(128), mime=True)

            model = get_model_for_mime_type(mime_type)

            m = model(
                owner=request.user,
                parent_id=serializer.validated_data['parent'],
                mime_type=mime_type,
                file=serializer.validated_data['file'],
            )
            m.save()

            return Response(m.pk)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
