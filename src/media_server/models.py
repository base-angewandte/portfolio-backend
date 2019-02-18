import json
import logging
import os
import shutil
import subprocess

import django_rq
import magic
from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from exiffield.fields import ExifField
from PIL import Image as PIL_Image, ImageOps

from core.models import Entity
from general.models import ShortUUIDField
from .storages import ProtectedFileSystemStorage

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
    entity_id = models.CharField(max_length=22)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    mime_type = models.CharField(blank=True, default='', max_length=255)
    exif = ExifField(source='file')
    published = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def metadata(self):
        remove = (
            'SourceFile',
            'ExifToolVersion',
            'FileName',
            'Directory',
            'FileModifyDate',
            'FileAccessDate',
            'FileInodeChangeDate',
            'FilePermissions',
        )
        ret = self.exif
        for k in remove:
            ret.pop(k, None)
        return ret

    @property
    def save_id(self):
        return self.id.replace(':', '')

    def convert(self, command):
        try:
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
        except Exception:
            logger.exception('Error while converting {}'.format(self.__class__.__name__.lower()))
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
            'published': self.published,
        }

    def get_mp3(self):
        return self.get_url('listen.mp3')

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        # convert
        script_path = os.path.join(settings.BASE_DIR, 'scripts', 'create-mp3.sh')
        path = self.file.path
        destination = self.get_protected_assets_path()

        self.convert(['/bin/bash', script_path, path, destination])


class Document(CommonInfo):
    id = ShortUUIDField(prefix=DOCUMENT_PREFIX, primary_key=True)

    def get_data(self):
        return {
            'id': self.pk,
            'thumbnail': self.get_preview_image(),
            'pdf': self.get_preview_pdf(),
            'original': self.file.url,
            'metadata': self.metadata,
            'published': self.published,
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


class Image(CommonInfo):
    id = ShortUUIDField(prefix=IMAGE_PREFIX, primary_key=True)
    file = models.ImageField(storage=ProtectedFileSystemStorage(), upload_to=user_directory_path)

    def convert(self, command=None):
        try:
            if self.status == STATUS_NOT_CONVERTED:
                self.status = STATUS_IN_PROGRESS
                self.save()

                path = self.get_protected_assets_path()
                if not os.path.exists(path):
                    os.makedirs(path)

                im = PIL_Image.open(self.file.path)
                if im.mode in ('RGBA', 'LA'):
                    fill_color = (255, 255, 255)
                    background = PIL_Image.new(im.mode[:-1], im.size, fill_color)
                    background.paste(im, im.split()[-1])
                    im = background
                im = ImageOps.fit(im, (400, 300), PIL_Image.ANTIALIAS)
                im.save(os.path.join(path, 'tn.jpg'))
                im.close()

                self.status = STATUS_CONVERTED
                self.save()
        except Exception:
            logger.exception('Error while converting {}'.format(self.__class__.__name__.lower()))
            self.status = STATUS_ERROR
            self.save()

    def get_data(self):
        return {
            'id': self.pk,
            'thumbnail': self.get_thumbnail(),
            'original': self.file.url,
            'metadata': self.metadata,
            'published': self.published,
        }

    def get_thumbnail(self):
        return self.get_url('tn.jpg')

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        # convert
        self.convert()


class Video(CommonInfo):
    id = ShortUUIDField(prefix=VIDEO_PREFIX, primary_key=True)

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
            'metadata': self.metadata,
            'published': self.published,
        }

    def get_playlist(self):
        return self.get_url('playlist.m3u8')

    def ffprobe(self):
        try:
            command = [
                "ffprobe",
                "-loglevel", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                self.file.path,
            ]

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = process.communicate()

            if process.returncode == 0:
                metadata = json.loads(out)
                metadata['format'].pop('filename')
                return metadata

        except OSError:
            pass

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        # convert
        script_path = os.path.join(settings.BASE_DIR, 'scripts', 'create-vod-hls.sh')
        path = self.file.path
        destination = self.get_protected_assets_path()

        self.convert(['/bin/bash', script_path, path, destination])


class Other(CommonInfo):
    id = ShortUUIDField(prefix=OTHER_PREFIX, primary_key=True)

    def get_data(self):
        return {
            'id': self.pk,
            'original': self.file.url,
            'metadata': self.metadata,
            'published': self.published,
        }

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()

        # convert
        # since we don't know what it is, we just set the status
        self.status = STATUS_CONVERTED
        self.save()


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


def get_media_for_entity(entity_id):
    ret = []
    for model in iter(PREFIX_TO_MODEL.values()):
        ret += model.objects.filter(entity_id=entity_id).values_list('pk', flat=True)
    return ret


def get_model_for_mime_type(mime_type):
    try:
        return MIME_TYPE_TO_MODEL[mime_type]
    except KeyError:
        return Other


def repair():
    for model in iter(PREFIX_TO_MODEL.values()):
        m = model.objects.filter(status__in=[STATUS_NOT_CONVERTED, STATUS_ERROR])
        for i in m:
            i.status = STATUS_NOT_CONVERTED
            i.save()
            django_rq.enqueue(i.media_info_and_convert)


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


@receiver(post_delete, sender=Entity)
def entity_post_delete(sender, instance, *args, **kwargs):
    for model in iter(PREFIX_TO_MODEL.values()):
        model.objects.filter(entity_id=instance.pk).delete()
