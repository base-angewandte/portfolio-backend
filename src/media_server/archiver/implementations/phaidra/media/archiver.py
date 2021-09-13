import json
import urllib

import requests
from rest_framework.exceptions import APIException

from django.utils import timezone

from core.models import Entry
from media_server.archiver import STATUS_ARCHIVE_ERROR, STATUS_ARCHIVED, credentials, uris
from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.factory.archives import Archives
from media_server.archiver.implementations.phaidra.exceptions import PhaidraServerError
from media_server.archiver.implementations.phaidra.media.datatranslation import PhaidraMediaDataTranslator
from media_server.archiver.implementations.phaidra.media.schemas import PhaidraMediaData
from media_server.archiver.implementations.phaidra.uris import (
    create_phaidra_object_create_uri,
    create_phaidra_update_url,
)
from media_server.archiver.interface.abstractarchiver import AbstractArchiver
from media_server.archiver.interface.archiveobject import ArchiveObject
from media_server.archiver.interface.responses import ModificationType, SuccessfulArchiveResponse
from media_server.models import Media


def _push_to_archive_job(media_object: 'Media'):
    entry_object: Entry = Entry.objects.get(id=media_object.entry_id)
    if not entry_object.archive_id:
        raise APIException({'Error': 'Entry {entry.id} not yet archived, cannot archive media %s'})
    media_archiver = MediaArchiver(
        archive_object=ArchiveObject(
            user=entry_object.owner,
            entry=entry_object,
            media_objects={
                media_object,
            },
        )
    )
    media_archiver.validate()
    media_archiver.push_to_archive()


def _update_archive_job(media_object: 'Media'):
    entry_object: Entry = Entry.objects.get(id=media_object.entry_id)
    if not entry_object.archive_id:
        raise APIException({'Error': 'Entry {entry.id} not yet archived, cannot archive media %s'})
    media_archiver = MediaArchiver(
        archive_object=ArchiveObject(
            user=entry_object.owner,
            entry=entry_object,
            media_objects={
                media_object,
            },
        )
    )
    media_archiver.validate()
    media_archiver.update_archive()


class MediaArchiveHandler(AbstractArchiver):
    """Handles many media archive jobs."""

    def push_to_archive(self) -> SuccessfulArchiveResponse:
        async_media_handler = AsyncMediaHandler(
            media_objects=self.archive_object.media_objects, job=_push_to_archive_job
        )
        async_media_handler.enqueue()
        file_names = [media_object.file.name for media_object in self.archive_object.media_objects]
        return SuccessfulArchiveResponse(
            ModificationType.uploaded,
            object_description='media ' + ', '.join(file_names),
            service=Archives.PHAIDRA.name,
        )

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        async_media_handler = AsyncMediaHandler(
            media_objects=self.archive_object.media_objects, job=_update_archive_job
        )
        async_media_handler.enqueue()
        file_names = [media_object.file.name for media_object in self.archive_object.media_objects]
        return SuccessfulArchiveResponse(
            ModificationType.updated,
            object_description='media ' + ', '.join(file_names),
            service=Archives.PHAIDRA.name,
        )

    def validate(self) -> None:
        """
        Nothing to validate here
        :return:
        """
        for media_object in self.archive_object.media_objects:
            entry_object = Entry.objects.get(id=media_object.entry_id)
            MediaArchiver(
                archive_object=ArchiveObject(
                    user=entry_object.owner,
                    entry=entry_object,
                    media_objects={
                        media_object,
                    },
                )
            ).validate()


class MediaArchiver(AbstractArchiver):
    """Handles Single Media Archive Job."""

    def __init__(self, archive_object: ArchiveObject):
        super().__init__(archive_object)
        self.media_object = next(iter(archive_object.media_objects))
        self.data = None

    def validate(self) -> None:
        translator = PhaidraMediaDataTranslator()
        data = translator.translate_data(self.media_object)
        schema = PhaidraMediaData()
        result = schema.load(data)
        errors: dict = result.errors
        self.data = schema.dump(result.data).data
        self.throw_validation_errors(translator.translate_errors(errors))

    def push_to_archive(self) -> SuccessfulArchiveResponse:
        if self.data is None:
            self.validate()
        self._check_for_consistency()
        media_push_response = self._push_to_archive()
        pid = self._handle_media_push_response(media_push_response)
        self._update_media(pid)
        link_entry_to_media_response = self.link_entry_to_media()
        self.handle_link_entry_to_media_response(link_entry_to_media_response)
        return SuccessfulArchiveResponse(
            modification_type=ModificationType.created,
            service='phaidra',
            object_description=f'Media <{self.media_object.archive_id}>',
        )

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        if self.data is None:
            self.validate()
        self._check_for_consistency()
        self._update_archive()
        return SuccessfulArchiveResponse(
            modification_type=ModificationType.updated,
            service='phaidra',
            object_description=f'Media <{self.media_object.archive_id}>',
        )

    def _push_to_archive(self) -> requests.Response:
        uri = create_phaidra_object_create_uri(self.media_object.mime_type)
        response = requests.post(
            uri,
            files={
                'metadata': json.dumps(self.data),
                'file': self.media_object.file,
            },
            auth=(credentials.get('USER'), credentials.get('PWD')),
        )

        return response

    def _update_archive(self) -> requests.Response:
        uri = create_phaidra_update_url(self.media_object.mime_type)
        response = requests.post(
            uri,
            files={
                'metadata': json.dumps(self.data),
            },
            auth=(credentials.get('USER'), credentials.get('PWD')),
        )
        return response

    def _handle_media_push_response(self, media_push_response: requests.Response) -> str:
        if media_push_response.status_code != 200:
            self.media_object.archive_status = STATUS_ARCHIVE_ERROR
            self.media_object.save()
        self._handle_external_server_response(media_push_response)
        try:
            return media_push_response.json()['pid'].strip()
        except KeyError:
            raise PhaidraServerError(f'NO PID returned in response, {media_push_response.content}')

    def _handle_external_server_response(self, response: requests.Response):
        if response.status_code != 200:
            raise PhaidraServerError(f'Response:\nStatus: {response.status_code}\nContent: {response.content}')

    def _update_media(self, pid: str) -> None:
        self.media_object.archive_URI = urllib.parse.urljoin(uris.get('IDENTIFIER_BASE'), pid)
        self.media_object.archive_id = pid
        self.media_object.archive_status = STATUS_ARCHIVED
        self.media_object.archive_date = timezone.now()
        self.media_object.save()

    def link_entry_to_media(self) -> requests.Response:
        uri = uris.get('BASE_URI') + f'object/{self.archive_object.entry.archive_id}/relationship/add'
        response = requests.post(
            uri,
            {'predicate': 'http://pcdm.org/models#hasMember', 'object': f'info:fedora/{self.media_object.archive_id}'},
            auth=(credentials.get('USER'), credentials.get('PWD')),
        )
        return response

    def handle_link_entry_to_media_response(self, link_entry_to_media_response: requests.Response):
        self._handle_external_server_response(link_entry_to_media_response)

    def _check_for_consistency(self):
        """
        Check for consistency between portfolio and phaidra: if the entry belonging to this media is not already
        archived, we can not archive the media
        :return:
        """
        if not self.archive_object.entry.archive_id:
            raise RuntimeError(
                f'Can not archive media <{self.media_object.id}>. '
                f'Entry <{self.archive_object.entry.id}> is not archived'
            )

        if self.media_object.archive_id:
            raise RuntimeWarning(f'Media <{self.media_object.id}> is already archived')
