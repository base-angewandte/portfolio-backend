import logging
import mimetypes
from os.path import basename, join

import magic
from PIL.Image import DecompressionBombError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.utils.translation import ugettext_lazy as _
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .decorators import is_allowed
from .models import PREFIX_TO_MODEL, get_model_for_mime_type
from .serializers import MediaCreateSerializer, MediaPartialUpdateSerializer
from .utils import check_quota

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
    parser_classes = (FormParser, MultiPartParser)
    serializer_class = MediaCreateSerializer

    action_serializers = {
        'create': MediaCreateSerializer,
        # 'update': MediaUpdateSerializer,
        'partial_update': MediaPartialUpdateSerializer,
    }

    def get_queryset(self):
        return None

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]

        return super(MediaViewSet, self).get_serializer_class()

    def _get_media_object(self, pk):
        model = PREFIX_TO_MODEL.get(pk[0])
        if model:
            try:
                return model.objects.get(id=pk)
            except model.DoesNotExist:
                pass

    def _update(self, request, pk=None, partial=False, *args, **kwargs):
        if pk:
            m = self._get_media_object(pk)

            if m:
                if m.owner != request.user:
                    return Response(
                        _('Current user is not the owner of this media object'),
                        status=status.HTTP_403_FORBIDDEN,
                    )

                serializer = self.get_serializer(data=request.data, partial=partial)

                if serializer.is_valid():
                    if serializer.validated_data:
                        model = PREFIX_TO_MODEL[pk[0]]
                        model.objects.filter(pk=m.pk).update(**serializer.validated_data)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(_('Media object does not exist'), status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(responses={
        200: openapi.Response(''),
        400: openapi.Response('Bad request'),
        415: openapi.Response('Unsupported media type'),
        422: openapi.Response('User quota exceeded'),
    })
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():

            if not check_quota(request.user, serializer.validated_data['file'].size):
                return Response(
                    _('No space left for user'),
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            mime_type = magic.from_buffer(serializer.validated_data['file'].read(1024000), mime=True)

            model = get_model_for_mime_type(mime_type)

            m = model(
                owner=request.user,
                entry_id=serializer.validated_data['entry'],
                mime_type=mime_type,
                file=serializer.validated_data['file'],
                published=serializer.validated_data['published'],
                license=serializer.validated_data.get('license') or None,
            )

            try:
                m.file.width
            except DecompressionBombError as dbe:
                msg = str(dbe)
                logger.exception(msg)
                return Response(msg, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            except AttributeError:
                # not an image
                pass
            except RuntimeError:
                # webp image
                # https://code.djangoproject.com/ticket/29705
                pass

            m.save()

            return Response(m.pk)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses={
        200: openapi.Response(''),
        202: openapi.Response('Media object is still converting'),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('Media object not found'),
    })
    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            m = self._get_media_object(pk)

            if m:
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

        return Response(_('Media object does not exist'), status=status.HTTP_404_NOT_FOUND)

    # @swagger_auto_schema(responses={
    #     204: openapi.Response(''),
    #     400: openapi.Response('Bad request'),
    #     403: openapi.Response('Access not allowed'),
    #     404: openapi.Response('Media object not found'),
    # })
    # def update(self, request, pk=None, *args, **kwargs):
    #     return self._update(request, pk=pk, partial=False, *args, **kwargs)

    @swagger_auto_schema(responses={
        204: openapi.Response(''),
        400: openapi.Response('Bad request'),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('Media object not found'),
    })
    def partial_update(self, request, pk=None, *args, **kwargs):
        return self._update(request, pk=pk, partial=True, *args, **kwargs)

    @swagger_auto_schema(responses={
        204: openapi.Response(''),
        403: openapi.Response('Access not allowed'),
        404: openapi.Response('Media object not found'),
    })
    def destroy(self, request, pk=None, *args, **kwargs):
        if pk:
            m = self._get_media_object(pk)

            if m:
                if m.owner != request.user:
                    return Response(
                        _('Current user is not the owner of this media object'),
                        status=status.HTTP_403_FORBIDDEN,
                    )

                m.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(_('Media object does not exist'), status=status.HTTP_404_NOT_FOUND)
