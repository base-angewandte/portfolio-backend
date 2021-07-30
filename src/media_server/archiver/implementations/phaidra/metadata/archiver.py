import json
import logging
from abc import ABC
from typing import TYPE_CHECKING, Dict, Optional
from urllib.parse import urljoin

import requests

from django.conf import settings

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.default.schemas import (
    _PhaidraMetaData,
    create_dynamic_phaidra_meta_data_schema,
)

from .... import credentials
from ....interface.exceptions import ExternalServerError
from ....interface.responses import ModificationType, SuccessfulArchiveResponse
from .mappings.contributormapping import BidirectionalConceptsMapper
from .thesis.datatranslation import PhaidraThesisMetaDataTranslator
from .thesis.schemas import _PhaidraThesisMetaDataSchema

if TYPE_CHECKING:
    from ....interface.archiveobject import ArchiveObject

from ....interface.abstractarchiver import AbstractArchiver


class DefaultMetadataArchiver(AbstractArchiver):

    data: Optional[Dict] = None
    mapper_class = BidirectionalConceptsMapper
    translator_class = PhaidraMetaDataTranslator
    base_schema_class = _PhaidraMetaData

    def __init__(self, archive_object: 'ArchiveObject'):
        super().__init__(archive_object)
        self.data = None
        self.is_update = None

    def validate(self) -> None:
        contributor_role_mapping = self.mapper_class.from_entry(self.archive_object.entry)
        translator = self.translator_class()
        data = translator.translate_data(self.archive_object.entry, contributor_role_mapping)
        schema = create_dynamic_phaidra_meta_data_schema(
            bidirectional_concepts_mapper=contributor_role_mapping, base_schema_class=self.base_schema_class
        )
        result = schema.load(data)
        errors: dict = result.errors
        self.data = schema.dump(result.data).data
        errors = translator.translate_errors(errors, contributor_role_mapping)
        self.throw_validation_errors(errors)

    def push_to_archive(self) -> 'SuccessfulArchiveResponse':
        if self.data is None:
            self.validate()
        self.is_update = self.archive_object.entry.archive_id is not None
        url = self._create_phaidra_url(self.archive_object.entry.archive_id)
        response = self._post_to_phaidra(url, self.data)
        return self._handle_phaidra_response(response)

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        return self.is_update()

    def _create_phaidra_url(self, archive_id: Optional[str] = None):
        if archive_id is None:
            return settings.ARCHIVE_URIS['CREATE_URI']
        base_uri = settings.ARCHIVE_URIS['CREATE_URI']
        return urljoin(base_uri, f'object/{archive_id}/metadata')

    def _post_to_phaidra(self, url, data: dict):
        data = json.dumps(data)
        logging.debug(f'Post to phaidra with metadata {data}')
        try:
            return requests.post(url, files={'metadata': data}, auth=(credentials.get('USER'), credentials.get('PWD')))
        except Exception as exception:
            raise ExternalServerError(exception)

    def _handle_phaidra_response(self, response: requests.Response) -> 'SuccessfulArchiveResponse':
        """
        :param response:
        :return:
        """
        pid = self._get_phaidra_pid(response)
        self._update_entry_archival_success_in_db(pid)
        return self._create_user_feedback(pid)

    def _get_phaidra_pid(self, response: requests.Response) -> str:
        if response.status_code != 200:
            raise RuntimeError(f'Phaidra returned with response {response} and content {response.content}')
        data = json.loads(response.content)
        return data['pid']

    def _update_entry_archival_success_in_db(self, pid: str):
        self.archive_object.entry.update_archive = False
        self.archive_object.entry.archive_id = pid
        self.archive_object.entry.archive_URI = urljoin(settings.ARCHIVE_URIS['IDENTIFIER_BASE'], pid)
        self.archive_object.entry.save(update_fields=['archive_URI', 'archive_id'])

    def _create_user_feedback(self, pid: str):
        return SuccessfulArchiveResponse(
            modification_type=ModificationType.updated if self.is_update else ModificationType.created,
            object_description=pid,
            service='PHAIDRA',
        )


class ThesisMetadataArchiver(DefaultMetadataArchiver, ABC):

    translator_class = PhaidraThesisMetaDataTranslator
    base_schema_class = _PhaidraThesisMetaDataSchema
