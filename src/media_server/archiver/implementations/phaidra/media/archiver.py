import json
from urllib.parse import urljoin
from typing import Dict

import requests
from rest_framework.exceptions import APIException

from django.utils import timezone

from core.models import Entry
from media_server.models import Media
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
from media_server.archiver.interface.archiveobject import ArchiveObject, ArchiveData
from media_server.archiver.interface.responses import ModificationType, SuccessfulArchiveResponse


def save_media_with_update(pk: str, fields: dict):
    return Media.objects.filter(pk=pk).update(**fields)


class MediaArchiver(AbstractArchiver):
    """Handles Single Media Archive Job."""

    @classmethod
    def from_archive_object(cls, archive_object: ArchiveObject) -> 'MediaArchiver':
        return cls(
            archive_object,
            ArchiveData(
                timezone.now(),
                PhaidraMediaDataTranslator().translate_data(next(iter(archive_object.media_objects)))
            )
        )

    def __init__(self, archive_object: ArchiveObject, archive_data: ArchiveData):
        super().__init__(archive_object)
        self.archive_data = archive_data
        self.media_object = next(iter(archive_object.media_objects))
        self.data = self.archive_data.data

    def validate(self) -> None:
        schema = PhaidraMediaData()
        result = schema.load(self.data)
        errors: dict = result.errors
        translator = PhaidraMediaDataTranslator()
        self.throw_validation_errors(translator.translate_errors(errors))

    def push_to_archive(self) -> SuccessfulArchiveResponse:
        self.validate()
        self._check_for_consistency()
        media_push_response = self._send_push_request_to_archive()
        self._handle_phaidra_error_response(media_push_response)
        self._save_phaidra_response(media_push_response, first_time=True)
        link_entry_to_media_response = self.link_entry_to_media()
        self._handle_phaidra_error_response(link_entry_to_media_response)
        return SuccessfulArchiveResponse(
            modification_type=ModificationType.created,
            service='phaidra',
            object_description=f'Media <{self.media_object.archive_id}>',
        )

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        self.validate()
        self._check_for_consistency()
        response = self._send_update_request_to_archive()
        self._handle_phaidra_error_response(response)
        self._save_phaidra_response(response, first_time=False)

        return SuccessfulArchiveResponse(
            modification_type=ModificationType.updated,
            service='phaidra',
            object_description=f'Media <{self.media_object.archive_id}>',
        )

    def _send_push_request_to_archive(self) -> requests.Response:
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

    def _send_update_request_to_archive(self) -> requests.Response:
        uri = create_phaidra_update_url(self.media_object.archive_id)
        response = requests.post(
            uri,
            files={
                'metadata': json.dumps(self.data),
            },
            auth=(credentials.get('USER'), credentials.get('PWD')),
        )
        return response

    def _handle_phaidra_error_response(self, phaidra_response: requests.Response,):
        if phaidra_response.status_code != 200:
            save_media_with_update(self.media_object.id, {'archive_status': STATUS_ARCHIVE_ERROR})
            raise PhaidraServerError(
                f'Phaidra Response:\n\tStatus: {phaidra_response.status_code}\n'
                f'\tContent: {phaidra_response.content}')

    def _save_phaidra_response(self, phaidra_response: requests.Response, first_time: bool) -> None:
        db_fields = {
            'archive_status': STATUS_ARCHIVED,
            'archive_date': self.archive_data.archive_date,
        }
        if first_time:
            try:
                pid = phaidra_response.json()['pid'].strip()
            except KeyError:
                raise PhaidraServerError(f'NO PID returned in response, {phaidra_response.content}')
            db_fields['archive_id'] = pid
            db_fields['archive_URI'] = urljoin(uris.get('IDENTIFIER_BASE'), pid)

        save_media_with_update(self.media_object.pk, db_fields)
        # Other methods expect this data to be on the media object itself, because before we used media.save()
        for field, value in db_fields.items():
            setattr(self.media_object, field, value)

    def link_entry_to_media(self) -> requests.Response:
        uri = uris.get('BASE_URI') + f'object/{self.archive_object.entry.archive_id}/relationship/add'
        response = requests.post(
            uri,
            {'predicate': 'http://pcdm.org/models#hasMember', 'object': f'info:fedora/{self.media_object.archive_id}'},
            auth=(credentials.get('USER'), credentials.get('PWD')),
        )
        return response

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


def _archive_job_commons(media_archiver: MediaArchiver) -> 'MediaArchiver':
    media_archiver.archive_object.entry.refresh_from_db()
    if not media_archiver.archive_object.entry:
        raise APIException({'Error': 'Entry {entry.id} not yet archived, cannot archive media %s'})
    media_archiver.validate()
    return media_archiver


def _push_to_archive_job(media_archiver: MediaArchiver):
    _archive_job_commons(media_archiver).push_to_archive()


def _update_archive_job(media_archiver: MediaArchiver):
    _archive_job_commons(media_archiver).update_archive()


class MediaArchiveHandler(AbstractArchiver):
    """Handles many media archive jobs."""

    generated_media_data: Dict[str, MediaArchiver]

    def __init__(self, archive_object: ArchiveObject):
        super().__init__(archive_object)
        self.generated_media_data = {}

    def generate_data(self):
        self.validate()
        if len(self.generated_media_data) != len(self.archive_object.media_objects):
            raise RuntimeError(
                f'len(self.generated_media_data) {len(self.generated_media_data)} '
                f'!= len(self.archive_object.media_objects) {len(self.archive_object.media_objects)}'
            )

    def _common_archival_job(self, first_time: bool):
        self.generate_data()
        job = _push_to_archive_job if first_time else _update_archive_job
        modification_type = ModificationType.created if first_time else ModificationType.updated
        async_media_handler = AsyncMediaHandler(
            media_archivers=set(self.generated_media_data.values()), job=job
        )
        async_media_handler.enqueue()
        file_names = [media_object.file.name for media_object in self.archive_object.media_objects]
        return SuccessfulArchiveResponse(
            modification_type,
            object_description='media ' + ', '.join(file_names),
            service=Archives.PHAIDRA.name,
        )

    def push_to_archive(self) -> SuccessfulArchiveResponse:
        return self._common_archival_job(True)

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        return self._common_archival_job(False)

    def validate(self) -> None:
        """
        :return:
        """
        for media_object in self.archive_object.media_objects:
            entry_object = Entry.objects.get(id=media_object.entry_id)
            archiver = MediaArchiver.from_archive_object(
                archive_object=ArchiveObject(
                    user=entry_object.owner,
                    entry=entry_object,
                    media_objects={
                        media_object,
                    },
                ),
            )
            self.generated_media_data[media_object.id] = archiver
