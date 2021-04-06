import logging
import mimetypes
from os.path import basename, join

import django_rq
import magic
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.static import serve

from core.models import Entry

from .archiver import archive_entry, archive_media
from .decorators import is_allowed
from .models import DOCUMENT_TYPE, STATUS_TO_BE_ARCHIVED, Media, get_type_for_mime_type
from .serializers import ArchiveSerializer, MediaCreateSerializer, MediaPartialUpdateSerializer
from .utils import check_quota

logger = logging.getLogger(__name__)


@is_allowed
@xframe_options_sameorigin
def protected_view(request, path, server):
    as_download = 'download' in request.GET.keys()
    if server == 'nginx':
        mimetype, encoding = mimetypes.guess_type(path)

        response = HttpResponse()

        response['Content-Type'] = mimetype

        if encoding:
            response['Content-Encoding'] = encoding

        if as_download:
            response['Content-Disposition'] = 'attachment; filename={}'.format(basename(path))

        response['X-Accel-Redirect'] = join(settings.PROTECTED_MEDIA_LOCATION, path).encode('utf8')
        return response

    elif server == 'django':
        return serve(request, path, document_root=settings.PROTECTED_MEDIA_ROOT, show_indexes=False)

    return HttpResponseServerError()


# DRF views

license_param = openapi.Parameter(
    'license',
    openapi.IN_FORM,
    description='media license json object',
    required=False,
    type=openapi.TYPE_STRING,
    **{'x-attrs': {'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'medialicenses'})}},
)


class MediaViewSet(viewsets.GenericViewSet):
    parser_classes = (FormParser, MultiPartParser)
    serializer_class = MediaCreateSerializer

    action_serializers = {
        'create': MediaCreateSerializer,
        # 'update': MediaUpdateSerializer,
        'partial_update': MediaPartialUpdateSerializer,
        'archive': ArchiveSerializer,
    }

    def get_queryset(self):
        return None

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]

        return super().get_serializer_class()

    def _get_media_object(self, pk):
        try:
            return Media.objects.get(id=pk)
        except Media.DoesNotExist:
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
                        Media.objects.filter(pk=m.pk).update(**serializer.validated_data)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(_('Media object does not exist'), status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(''),
            400: openapi.Response('Bad request'),
            415: openapi.Response('Unsupported media type'),
            422: openapi.Response('User quota exceeded'),
        },
        manual_parameters=[license_param],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():

            if not check_quota(request.user, serializer.validated_data['file'].size):
                return Response(
                    _('No space left for user'),
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            mime_type = magic.from_buffer(serializer.validated_data['file'].read(1048576), mime=True)
            media_type = get_type_for_mime_type(mime_type)

            if mime_type in ['application/octet-stream', 'application/zip']:
                # check for office document
                serializer.validated_data['file'].seek(0)
                magic_type = magic.from_buffer(serializer.validated_data['file'].read(1048576))
                if magic_type in [
                    'Microsoft Word 2007+',
                    'Microsoft PowerPoint 2007+',
                    'Microsoft Excel 2007+',
                    'Microsoft OOXML',
                ]:
                    media_type = DOCUMENT_TYPE

            m = Media(
                file=serializer.validated_data['file'],
                type=media_type,
                owner=request.user,
                entry_id=serializer.validated_data['entry'],
                mime_type=mime_type,
                published=serializer.validated_data['published'],
                license=serializer.validated_data.get('license') or None,
            )

            m.save()

            return Response(m.pk)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(''),
            202: openapi.Response('Media object is still converting'),
            403: openapi.Response('Access not allowed'),
            404: openapi.Response('Media object not found'),
        }
    )
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
                    return Response({'id': pk}, status=status.HTTP_202_ACCEPTED)

                return Response(m.get_data())

        return Response(_('Media object does not exist'), status=status.HTTP_404_NOT_FOUND)

    # @swagger_auto_schema(responses={
    #     204: openapi.Response(''),
    #     400: openapi.Response('Bad request'),
    #     403: openapi.Response('Access not allowed'),
    #     404: openapi.Response('Media object not found'),
    # }, manual_parameters=[license_param])
    # def update(self, request, pk=None, *args, **kwargs):
    #     return self._update(request, pk=pk, partial=False, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            204: openapi.Response(''),
            400: openapi.Response('Bad request'),
            403: openapi.Response('Access not allowed'),
            404: openapi.Response('Media object not found'),
        },
        manual_parameters=[license_param],
    )
    def partial_update(self, request, pk=None, *args, **kwargs):
        return self._update(request, pk=pk, partial=True, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            204: openapi.Response(''),
            403: openapi.Response('Access not allowed'),
            404: openapi.Response('Media object not found'),
        }
    )
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

    @swagger_auto_schema(
        responses={
            204: openapi.Response(''),
            400: openapi.Response('Error archiving to Phaidra'),
            403: openapi.Response('Access not allowed'),
            404: openapi.Response('Media object not found'),
        },
        manual_parameters=[
            openapi.Parameter(
                'templatename',
                openapi.IN_QUERY,
                required=False,
                description='template file name to map metadata to archival system',
                default=settings.ARCHIVE_METADATA_TEMPLATE,
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    @action(detail=True)
    def archive(self, request, pk=None, *args, **kwargs):
        template_name = request.query_params.get('templatename', settings.ARCHIVE_METADATA_TEMPLATE)
        try:
            media = Media.objects.get(pk=pk)
            if not media.file:
                raise Media.DoesNotExist
            if media.owner != request.user:
                raise exceptions.PermissionDenied(_('Current user is not the owner of this media'))

            ret = archive_entry(media.entry_id, template_name)
            if not ret.get('entry_pid'):
                return Response(ret)

            ret = archive_media(media)
            return Response(ret)
        except Media.DoesNotExist:
            raise exceptions.NotFound(_('Media does not exist'))
        except Exception as e:
            # Show where it failed? i.e. in the container creation or member creation?
            logging.warning("Encountered %s", repr(e))
            raise exceptions.APIException(_('Error archiving media asset'))


@swagger_auto_schema(
    methods=['get'],
    operation_id='api_v1_archive_assets',
    responses={
        200: openapi.Response(''),
        400: openapi.Response('Bad request'),
        403: openapi.Response('Access not allowed'),
    },
    manual_parameters=[
        openapi.Parameter(
            'template_name',
            openapi.IN_QUERY,
            required=False,
            description='template file name to map metadata to archival system',
            default=settings.ARCHIVE_METADATA_TEMPLATE,
            type=openapi.TYPE_STRING,
        ),
    ],
)
@api_view(['GET'])
def archive_assets(request, media_pks, *args, **kwargs):
    """
    # @entry_pk: entry pk
    @media_pks: comma separated list of media pks
    Expected all media pks from the same entry - owned by the user
    """
    # remove duplicate media ids from request
    media_ids = [pk.strip() for pk in list(set(media_pks.split(',')))]
    ## check if all assets belong to the same entry
    try:
        media_objects = [Media.objects.get(id=pk) for pk in media_ids]
    except Media.DoesNotExist:
        return Response(
            _('Media assets do not exist'),
            status=status.HTTP_400_BAD_REQUEST,
        )

    entry_pk = media_objects[0].entry_id
    entry = Entry.objects.get(id=entry_pk)
    if not all([entry_pk == m.entry_id for m in media_objects]):
        return Response(
            _('Media assets do not share the same metadata'),
            status=status.HTTP_400_BAD_REQUEST,
        )

    if entry.owner != request.user:
        return Response(
            _('Current user is not the owner of this media object'),
            status=status.HTTP_403_FORBIDDEN,
        )
    template_name = request.GET.get('template_name', settings.ARCHIVE_METADATA_TEMPLATE)

    # Archive the entry first, get the container pid
    entry_res = archive_entry(entry_pk, template_name)
    if not entry_res.get('entry_pid'):
        return Response(entry_res)

    # archive the media objects asynchronously
    # Media.objects.filter(pk__in=media_ids).update(archive_status=STATUS_TO_BE_ARCHIVED)
    queue = django_rq.get_queue('high')
    for m in media_objects:
        # Trigger saving in the background
        queue.enqueue(archive_media, m)
        # archive_media.delay(m)

    return Response(
        {
            'entry': entry_pk,
            'media_ids': media_ids,
            'entry_pid': entry.archive_id,
        }
    )
