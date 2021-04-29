import json
import logging
import os
import shutil
import subprocess  # nosec

import django_rq
import magic
from rq.command import send_stop_job_command
from rq.exceptions import InvalidJobOperation, NoSuchJobError
from rq.job import Job

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.db.models import IntegerField, Value
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.models import Entry
from general.models import ShortUUIDField

from .apps import MediaServerConfig
from .archiver import ARCHIVE_STATUS_CHOICES, STATUS_NOT_ARCHIVED, archive_entry, archive_media
from .storages import ProtectedFileSystemStorage
from .utils import humanize_size, user_hash
from .validators import validate_license

SCRIPTS_BASE_DIR = os.path.join(settings.BASE_DIR, MediaServerConfig.name, 'scripts')
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

AUDIO_TYPE = 'a'
DOCUMENT_TYPE = 'd'
IMAGE_TYPE = 'i'
VIDEO_TYPE = 'v'
OTHER_TYPE = 'x'
TYPE_CHOICES = (
    (AUDIO_TYPE, 'audio'),
    (DOCUMENT_TYPE, 'document'),
    (IMAGE_TYPE, 'image'),
    (VIDEO_TYPE, 'video'),
    (OTHER_TYPE, 'other'),
)

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
    return '{}/{}'.format(user_hash(instance.owner.username), filename)


class Media(models.Model):
    id = ShortUUIDField(primary_key=True)
    file = models.FileField(storage=ProtectedFileSystemStorage(), upload_to=user_directory_path)
    type = models.CharField(choices=TYPE_CHOICES, max_length=1, default=OTHER_TYPE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entry_id = models.CharField(max_length=22)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    mime_type = models.CharField(blank=True, default='', max_length=255)
    exif = JSONField(default=dict)
    published = models.BooleanField(default=False)
    license = JSONField(validators=[validate_license], blank=True, null=True)
    archive_id = models.CharField(max_length=255, default='')
    archive_URI = models.CharField(max_length=255, default='')
    archive_status = models.IntegerField(choices=ARCHIVE_STATUS_CHOICES, default=STATUS_NOT_ARCHIVED)

    class Meta:
        indexes = [
            models.Index(fields=['entry_id']),
        ]
        ordering = ['-created']

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

    def convert(self, command):
        try:
            if self.status == STATUS_NOT_CONVERTED:
                self.status = STATUS_IN_PROGRESS
                self.save()

                process = subprocess.run(command, stderr=subprocess.PIPE)  # nosec

                if process.returncode == 0:
                    self.status = STATUS_CONVERTED
                    self.save()
                else:
                    logger.error(
                        'Error while converting {}:\n{}'.format(
                            dict(TYPE_CHOICES).get(self.type),
                            process.stderr.decode('utf-8'),
                        )
                    )
                    self.status = STATUS_ERROR
                    self.save()
        except Exception:
            logger.exception('Error while converting {}'.format(dict(TYPE_CHOICES).get(self.type)))
            self.status = STATUS_ERROR
            self.save()

    def get_protected_assets_path(self):
        return os.path.join(os.path.dirname(self.file.path), self.id)

    def get_protected_assets_url(self):
        return self.file.storage.url(user_directory_path(self, self.id))

    def get_image(self):
        if self.type == DOCUMENT_TYPE:
            return self.get_url('preview.jpg')
        elif self.type == IMAGE_TYPE:
            return self.get_url('tn.jpg')
        elif self.type == VIDEO_TYPE:
            return self.get_url('cover.jpg')

    def get_previews(self):
        ret = []
        if self.check_file('preview.txt'):
            with open(self.get_file_path('preview.txt')) as f:
                for line in f:
                    k, v = line.rstrip('\n').split(',')
                    ret.append({f'{k}w': self.get_url(v)})
        return ret

    def get_data(self):
        data = {
            'id': self.pk,
            'type': self.type,
            'original': self.file.url,
            'metadata': self.metadata,
            'published': self.published,
            'license': self.license,
            'archive_id': self.archive_id,
            'archive_URI': self.archive_URI,
        }
        if self.type == AUDIO_TYPE:
            data.update({'mp3': self.get_url('listen.mp3')})
        elif self.type == DOCUMENT_TYPE:
            data.update({'thumbnail': self.get_image(), 'pdf': self.get_url('preview.pdf')})
        elif self.type == IMAGE_TYPE:
            data.update({'thumbnail': self.get_image(), 'previews': self.get_previews()})
        elif self.type == VIDEO_TYPE:
            data.update(
                {
                    'cover': {'gif': self.get_url('cover.gif'), 'jpg': self.get_image()},
                    'playlist': self.get_url('playlist.m3u8'),
                }
            )

        return data

    def get_file_path(self, filename):
        return os.path.join(self.get_protected_assets_path(), filename)

    def check_file(self, filename):
        path = self.get_file_path(filename)
        return os.path.isfile(path)

    def get_url(self, filename):
        if isinstance(filename, str):
            filename = [filename]

        for f in filename:
            if self.check_file(f):
                return f'{self.get_protected_assets_url()}/{f}'

        logger.error('File {} does not exist for {}'.format(', '.join(filename), self.id))
        return None

    def media_info_and_convert(self):
        # media info
        self.set_mime_type()
        self.set_exif()
        self.check_mime_type()

        # convert
        path = self.file.path
        destination = self.get_protected_assets_path()

        if self.type == DOCUMENT_TYPE:
            script_path = os.path.join(SCRIPTS_BASE_DIR, 'create-preview.sh')
            self.convert(['/bin/bash', script_path, settings.LOOL_HOST, path, destination])
        else:
            if self.type == AUDIO_TYPE:
                script_path = os.path.join(SCRIPTS_BASE_DIR, 'create-mp3.sh')
            elif self.type == IMAGE_TYPE:
                script_path = os.path.join(SCRIPTS_BASE_DIR, 'create-tn.sh')
            elif self.type == VIDEO_TYPE:
                script_path = os.path.join(SCRIPTS_BASE_DIR, 'create-vod-hls.sh')
            else:
                # since we don't know what it is, we just set the status
                self.status = STATUS_CONVERTED
                self.save()
                script_path = None

            if script_path:
                self.convert(['/bin/bash', script_path, path, destination])

    def check_mime_type(self):
        exiftool_mime_type = self.exif.get('MIMEType', {}).get('val')
        if exiftool_mime_type and self.mime_type != exiftool_mime_type:
            logger.warning(f'MIMEType mismatch: {self.mime_type} != {exiftool_mime_type}')
            # correct some mime types
            if self.mime_type in [
                'application/zip',
                'video/x-ms-asf',
            ]:
                self.mime_type = exiftool_mime_type
                self.type = get_type_for_mime_type(self.mime_type)

    def set_mime_type(self):
        self.file.open()
        mime_type = magic.from_buffer(self.file.read(1048576), mime=True)
        self.file.close()
        self.mime_type = mime_type
        self.save()

    def set_exif(self):
        try:
            self.exif = json.loads(subprocess.check_output(['exiftool', '-j', '-l', '-b', self.file.path]))[0]  # nosec
        except Exception:
            logger.warning('Could not read metainformation from file: %s', self.file.path)
            # create fallback data
            self.exif = {
                'FileSize': {'desc': 'File Size', 'num': self.file.size, 'val': humanize_size(self.file.size)},
                'MIMEType': {'desc': 'MIME Type', 'val': self.mime_type},
            }
        self.save()

    def get_job_id(self):
        return f'job_media_info_and_convert_{self.pk}'

    def get_archive_job_id(self):
        return f'job_archive_{self.pk}'


MIME_TYPE_TO_TYPE = {
    **{k: AUDIO_TYPE for k in AUDIO_MIME_TYPES},
    **{k: DOCUMENT_TYPE for k in DOCUMENT_MIME_TYPES},
    **{k: IMAGE_TYPE for k in IMAGE_MIME_TYPES},
    **{k: VIDEO_TYPE for k in VIDEO_MIME_TYPES},
}


def has_entry_media(entry_id):
    return Media.objects.filter(entry_id=entry_id).exists()


def get_media_for_entry(entry_id, flat=True, published=None):
    if flat:
        return Media.objects.filter(entry_id=entry_id).values_list('pk', flat=True)

    ret = []
    exclude = []

    query = Media.objects.filter(entry_id=entry_id, status=STATUS_CONVERTED)
    if published is not None:
        query = query.filter(published=published)

    for m in query:
        exclude.append(m.pk)
        data = m.get_data()
        data.update({'response_code': 200})
        ret.append(data)

    query = Media.objects.filter(entry_id=entry_id).exclude(id__in=exclude)
    if published is not None:
        query = query.filter(published=published)

    ret += list(
        query.annotate(response_code=Value(202, IntegerField())).values(
            'id', 'archive_id', 'archive_URI', 'response_code'
        )
    )

    return ret


def get_image_for_entry(entry_id):
    for m in Media.objects.filter(entry_id=entry_id, status=STATUS_CONVERTED).order_by('created'):
        if m.get_image():
            return m.get_image()


def get_type_for_mime_type(mime_type):
    try:
        return MIME_TYPE_TO_TYPE[mime_type]
    except KeyError:
        return OTHER_TYPE


def repair():
    for m in Media.objects.filter(status__in=[STATUS_NOT_CONVERTED, STATUS_ERROR]):
        m.status = STATUS_NOT_CONVERTED
        m.save()
        queue = django_rq.get_queue('high')
        queue.enqueue(m.media_info_and_convert, job_id=m.get_job_id(), failure_ttl=settings.RQ_FAILURE_TTL)


# Signal handling


@receiver(post_save, sender=Media)
def media_post_save(sender, instance, created, *args, **kwargs):
    if created:
        if instance.type == VIDEO_TYPE:
            queue = django_rq.get_queue('video')
            with transaction.atomic():
                # ensure status is STATUS_NOT_CONVERTED
                sender.objects.filter(pk=instance.pk).update(status=STATUS_NOT_CONVERTED)
                transaction.on_commit(
                    lambda: queue.enqueue(
                        instance.media_info_and_convert,
                        job_id=instance.get_job_id(),
                        failure_ttl=settings.RQ_FAILURE_TTL,
                    )
                )
        else:
            with transaction.atomic():
                # ensure status is STATUS_NOT_CONVERTED
                sender.objects.filter(pk=instance.pk).update(status=STATUS_NOT_CONVERTED)
                transaction.on_commit(
                    lambda: django_rq.enqueue(
                        instance.media_info_and_convert,
                        job_id=instance.get_job_id(),
                        failure_ttl=settings.RQ_FAILURE_TTL,
                    )
                )


@receiver(pre_delete, sender=Media)
def media_pre_delete(sender, instance, *args, **kwargs):
    conn = django_rq.get_connection()
    try:
        job = Job.fetch(instance.get_job_id(), connection=conn)
        if job.get_status() == 'started':
            try:
                send_stop_job_command(conn, instance.get_job_id())
            except InvalidJobOperation:
                pass
            job.delete()
    except NoSuchJobError:
        pass
    try:
        archive_job = Job.fetch(instance.get_archive_job_id(), connection=conn)
        if job.get_status() == 'started':
            try:
                send_stop_job_command(conn, instance.get_archive_job_id())
            except InvalidJobOperation:
                pass
            archive_job.delete()
    except NoSuchJobError:
        pass


@receiver(post_delete, sender=Media)
def media_post_delete(sender, instance, *args, **kwargs):
    try:
        shutil.rmtree(instance.get_protected_assets_path())
    except FileNotFoundError:
        pass


@receiver(post_delete, sender=Entry)
def entry_post_delete(sender, instance, *args, **kwargs):
    Media.objects.filter(entry_id=instance.pk).delete()


@receiver(pre_save, sender=Entry)
def entry_pre_save(sender, instance, update_fields, *args, **kwargs):
    if instance.archive_id:
        # Update the metadata in the archived asset
        res = archive_entry(instance)
        if res.get('Error'):
            raise ValueError(res.get('Error'))
    else:
        pass
