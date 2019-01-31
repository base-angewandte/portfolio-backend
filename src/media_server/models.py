import logging
import os
import shutil
import subprocess

import audio_metadata
import audioread
import exifread
import django_rq
import magic
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from PIL import Image as PIL_Image, ImageOps

from general.models import ShortUUIDField
from .storages import ProtectedFileSystemStorage
from .utils import convert_to_degress

STATUS_NOT_CONVERTED = 0
STATUS_IN_PROGRESS = 1
STATUS_CONVERTED = 2
STATUS_ERROR = 3
STATUS_CHOICES = (
    (STATUS_NOT_CONVERTED, 'not converted'),
    (STATUS_IN_PROGRESS, 'in progress'),
    (STATUS_CONVERTED, 'converted'),
    (STATUS_ERROR, 'error'),
)

AUDIO_PREFIX = 'a'
DOCUMENT_PREFIX = 'd'
IMAGE_PREFIX = 'i'
VIDEO_PREFIX = 'v'
OTHER_PREFIX = 'x'

AUDIO_MIME_TYPES = [
    'audio/aiff',
    'audio/aac',
    'audio/midi',
    'audio/mpeg',
    'audio/mp4',
    'audio/ogg',
    'audio/wav',
    'audio/x-wav',
    'audio/x-ms-wma',
    'audio/flac',
    'audio/x-matroska',
    'audio/basic',
]
DOCUMENT_MIME_TYPES = [
    'application/pdf',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.oasis.opendocument.presentation',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.ms-excel',
    'application/vnd.ms-powerpoint',
    'application/vnd.ms-word',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/rtf',
]
IMAGE_MIME_TYPES = [
    'image/bmp',
    'image/gif',
    'image/jpeg',
    'image/jp2',
    'image/png',
    'image/webp',
    'image/x-icon',
    'image/vnd.adobe.photoshop',
    'image/tiff',
]
VIDEO_MIME_TYPES = [
    'video/3gpp2',
    'video/3gpp',
    'video/avi',
    'video/x-flv',
    'video/mp4',
    'video/x-matroska',
    'video/quicktime',
    'video/mpeg',
    'video/dvd',
    'video/x-ms-wmv',
    'video/x-ms-asf',
    'video/ogg',
    'video/webm',
]

logger = logging.getLogger(__name__)


def user_directory_path(instance, filename):
    return '{}/{}/{}'.format(settings.HASHIDS.encode(instance.owner.id), instance.__class__.__name__.lower(), filename)


class CommonInfo(models.Model):
    id = ShortUUIDField(primary_key=True)
    file = models.FileField(storage=ProtectedFileSystemStorage(), upload_to=user_directory_path)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, on_delete=models.CASCADE)
    parent_id = models.CharField(max_length=22)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    mime_type = models.CharField(blank=True, default='', max_length=255)
    metadata = JSONField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def save_id(self):
        return self.id.replace(':', '')

    def convert(self, command):
        if self.status == STATUS_NOT_CONVERTED:
            self.status = STATUS_IN_PROGRESS
            self.save()

            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                out, err = process.communicate()

                if process.returncode == 0:
                    self.status = STATUS_CONVERTED
                    self.save()
                else:
                    self.status = STATUS_ERROR
                    self.save()

            except OSError:
                self.status = STATUS_ERROR
                self.save()

    def get_protected_assets_path(self):
        return os.path.join(os.path.dirname(self.file.path), self.save_id)

    def get_protected_assets_url(self):
        return self.file.storage.url(user_directory_path(self, self.save_id))

    def get_data(self):
        pass

    def check_file(self, filename):
        path = os.path.join(self.get_protected_assets_path(), filename)
        return os.path.isfile(path)

    def get_url(self, filename):
        if self.check_file(filename):
            return '{}/{}'.format(self.get_protected_assets_url(), filename)
        else:
            logger.error('File {} does not exist for {}'.format(filename, self.id))
            return None

    def media_info_and_convert(self):
        pass

    def set_mime_type(self):
        self.file.open()
        mime_type = magic.from_buffer(self.file.read(1024000), mime=True)
        self.file.close()
        self.mime_type = mime_type
        self.save()


# Models

class Audio(CommonInfo):
    id = ShortUUIDField(prefix=AUDIO_PREFIX, primary_key=True)

    def get_data(self):
        return {
            'id': self.pk,
            'mp3': self.get_mp3(),
            'original': self.file.url,
            'metadata': self.metadata,
        }

    def get_mp3(self):
        return self.get_url('listen.mp3')

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        streaminfo = {}
        tags = None

        try:
            metadata = audio_metadata.load(self.file.path)
            streaminfo = {k: v for k, v in sorted(metadata.streaminfo.items()) if not k.startswith('_')}
            tags = {
                metadata.tags.FIELD_MAP.inv.get(k, k): v[0] if len(v) == 1 else v
                for k, v in metadata.tags.__dict__.items()
                if not k.startswith('_')
            }
        except audio_metadata.UnsupportedFormat:
            try:
                with audioread.audio_open(self.file.path) as f:
                    streaminfo = {
                        'channels': f.channels,
                        'sample_rate': f.samplerate,
                        'duration': f.duration,
                    }
            except audioread.DecodeError:
                pass

        if streaminfo or tags:
            tags = {'tags': tags} if tags else {}
            self.metadata = {
                **streaminfo,
                **tags,
            }
            self.save()

        # convert
        script_path = os.path.join(settings.BASE_DIR, 'scripts', 'create-mp3.sh')
        path = self.file.path
        destination = self.get_protected_assets_path()

        self.convert(['/bin/bash', script_path, path, destination])


class Document(CommonInfo):
    id = ShortUUIDField(prefix=DOCUMENT_PREFIX, primary_key=True)
    # TODO add metadata fields

    def get_data(self):
        return {
            'id': self.pk,
            'tn': self.get_preview_image(),
            'pdf': self.get_preview_pdf(),
            'original': self.file.url,
        }

    def get_preview_image(self):
        return self.get_url('preview.jpg')

    def get_preview_pdf(self):
        return self.get_url('preview.pdf')

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        # convert
        script_path = os.path.join(settings.BASE_DIR, 'scripts', 'create-preview.sh')
        path = self.file.path
        destination = self.get_protected_assets_path()

        self.convert(['/bin/bash', script_path, settings.LOOL_HOST, path, destination])

        self.status = STATUS_CONVERTED
        self.save()


class Image(CommonInfo):
    id = ShortUUIDField(prefix=IMAGE_PREFIX, primary_key=True)
    file = models.ImageField(storage=ProtectedFileSystemStorage(), upload_to=user_directory_path)
    # TODO add metadata fields

    def convert(self, command=None):
        if self.status == STATUS_NOT_CONVERTED:
            self.status = STATUS_IN_PROGRESS
            self.save()

            path = self.get_protected_assets_path()
            if not os.path.exists(path):
                os.makedirs(path)

            im = PIL_Image.open(self.file.path)
            im = ImageOps.fit(im, (400, 300), PIL_Image.ANTIALIAS)
            im.save(os.path.join(path, 'tn.jpg'))
            im.close()

            self.status = STATUS_CONVERTED
            self.save()

    def get_data(self):
        return {
            'id': self.pk,
            'thumbnail': self.get_thumbnail(),
            'original': self.file.url,
            'metadata': self.metadata,
        }

    def get_thumbnail(self):
        return self.get_url('tn.jpg')

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        self.file.open()
        exif = exifread.process_file(self.file)
        self.file.close()

        exif_dict = {
            k: v.printable for k, v in exif.items() if isinstance(v, exifread.classes.IfdTag)
        } if exif else None

        lat = None
        lon = None

        gps_latitude = exif.get('GPS GPSLatitude')
        gps_latitude_ref = exif.get('GPS GPSLatitudeRef')
        gps_longitude = exif.get('GPS GPSLongitude')
        gps_longitude_ref = exif.get('GPS GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = convert_to_degress(gps_latitude)
            if gps_latitude_ref.values[0] != 'N':
                lat = -lat

            lon = convert_to_degress(gps_longitude)
            if gps_longitude_ref.values[0] != 'E':
                lon = - lon

        self.metadata = {
            'width': self.file.width,
            'height': self.file.height,
            'gps': {'lat': lat, 'lon': lon} if lat and lon else None,
            'exif': exif_dict,
        }
        self.save()

        # convert
        self.convert()


class Video(CommonInfo):
    id = ShortUUIDField(prefix=VIDEO_PREFIX, primary_key=True)
    # TODO add metadata fields

    def get_cover_gif(self):
        return self.get_url('cover.gif')

    def get_cover_jpg(self):
        return self.get_url('cover.jpg')

    def get_data(self):
        return {
            'id': self.pk,
            'cover': {
                'gif': self.get_cover_gif(),
                'jpg': self.get_cover_jpg(),
            },
            'playlist': self.get_playlist(),
            'original': self.file.url,
        }

    def get_playlist(self):
        return self.get_url('playlist.m3u8')

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        # convert
        script_path = os.path.join(settings.BASE_DIR, 'scripts', 'create-vod-hls.sh')
        path = self.file.path
        destination = self.get_protected_assets_path()

        self.convert(['/bin/bash', script_path, path, destination])

        # result = subprocess.Popen(
        #     ["ffprobe", path],
        #     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        #     encoding='utf-8'
        # )
        #
        # for x in result.stdout.readlines():
        #     pass

        # if self.status == STATUS_NOT_CONVERTED:
        #     self.status = STATUS_IN_PROGRESS
        #     self.save()
        #
        #     script_path = os.path.join(settings.BASE_DIR, 'scripts', 'create-vod-hls.sh')
        #     path = self.file.path
        #     destination = self.get_protected_assets_path()
        #
        #     try:
        #         process = subprocess.Popen(
        #             ['/bin/bash', script_path, path, destination],
        #             stdout=subprocess.PIPE,
        #             stderr=subprocess.PIPE,
        #         )
        #
        #         out, err = process.communicate()
        #
        #         if process.returncode == 0:
        #             # p = subprocess.Popen(
        #             #     ['mediainfo', "'--Inform=Video;%Width%'", path],
        #             #     stdout=subprocess.PIPE,
        #             #     stderr=subprocess.PIPE,
        #             # )
        #             #
        #             # stdout, stderr = p.communicate()
        #             # if p.wait() == 0:
        #             #     print(int(stdout.decode('utf8').strip(' \t\n\r')))
        #             #     self.width = int(stdout.decode('utf8').strip(' \t\n\r'))
        #             #
        #             # p = subprocess.Popen(
        #             #     ['mediainfo', "'--Inform=Video;%Height%'", path],
        #             #     stdout=subprocess.PIPE,
        #             #     stderr=subprocess.PIPE,
        #             # )
        #             #
        #             # stdout, stderr = p.communicate()
        #             # if p.wait() == 0:
        #             #     self.height = int(stdout.decode('utf8').strip(' \t\n\r'))
        #
        #             self.status = STATUS_CONVERTED
        #             self.save()
        #         else:
        #             self.status = STATUS_ERROR
        #             self.save()
        #
        #     except OSError:
        #         self.status = STATUS_ERROR
        #         self.save()


class Other(CommonInfo):
    id = ShortUUIDField(prefix=OTHER_PREFIX, primary_key=True)
    # TODO add metadata fields

    def get_data(self):
        return {
            'id': self.pk,
            'original': self.file.url,
        }

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        # convert
        # since we don't know what it is,  we just set the status
        self.status = STATUS_CONVERTED
        self.save()


# Signal handling

@receiver(post_save, sender=Audio)
@receiver(post_save, sender=Document)
@receiver(post_save, sender=Image)
@receiver(post_save, sender=Video)
@receiver(post_save, sender=Other)
def media_post_save(sender, instance, created, *args, **kwargs):
    if created:
        with transaction.atomic():
            # ensure status is STATUS_NOT_CONVERTED
            sender.objects.filter(pk=instance.pk).update(status=STATUS_NOT_CONVERTED)
            transaction.on_commit(lambda: django_rq.enqueue(instance.media_info_and_convert))


@receiver(post_delete, sender=Audio)
@receiver(post_delete, sender=Document)
@receiver(post_delete, sender=Image)
@receiver(post_delete, sender=Video)
@receiver(post_delete, sender=Other)
def media_post_delete(sender, instance, *args, **kwargs):
    try:
        shutil.rmtree(instance.get_protected_assets_path())
    except FileNotFoundError:
        pass


PREFIX_TO_MODEL = {
    AUDIO_PREFIX: Audio,
    DOCUMENT_PREFIX: Document,
    IMAGE_PREFIX: Image,
    VIDEO_PREFIX: Video,
    OTHER_PREFIX: Other,
}

MIME_TYPE_TO_MODEL = {
    **{k: Audio for k in AUDIO_MIME_TYPES},
    **{k: Document for k in DOCUMENT_MIME_TYPES},
    **{k: Image for k in IMAGE_MIME_TYPES},
    **{k: Video for k in VIDEO_MIME_TYPES},
}


def get_media_for_parent(request, parent_id):
    ret = []
    for model in iter(PREFIX_TO_MODEL.values()):
        ret += model.objects.filter(owner=request.user, parent_id=parent_id).values_list('pk', flat=True)
    return ret


def get_model_for_mime_type(mime_type):
    try:
        return MIME_TYPE_TO_MODEL[mime_type]
    except KeyError:
        return Other
