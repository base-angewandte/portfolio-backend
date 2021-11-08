import json
import logging
from typing import TYPE_CHECKING, Dict, Optional
from urllib.parse import urljoin

import requests

from django.conf import settings
from django.utils import timezone

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.default.schemas import PhaidraMetaData

from .... import credentials
from ....interface.exceptions import ExternalServerError
from ....interface.responses import ModificationType, SuccessfulArchiveResponse
from ..uris import create_phaidra_update_url
from .mappings.contributormapping import BidirectionalConceptsMapper
from .thesis.datatranslation import PhaidraThesisMetaDataTranslator
from .thesis.schemas import PhaidraThesisContainer, create_dynamic_phaidra_thesis_meta_data_schema

if TYPE_CHECKING:
    from ....interface.archiveobject import ArchiveObject
    from core.models import Entry

from ....interface.abstractarchiver import AbstractArchiver


class DefaultMetadataArchiver(AbstractArchiver):
    data: Optional[Dict] = None

    def __init__(self, archive_object: 'ArchiveObject'):
        super().__init__(archive_object)
        self.data = None
        self.is_update = None
        self._schema = None
        self._translator = None

    def validate(self) -> None:
        self.data = self._translate_data(self.archive_object.entry)
        schema = self.schema
        result = schema.load(self.data)
        errors: dict = result.errors
        errors = self._translate_errors(errors)
        self.throw_validation_errors(errors)

    def push_to_archive(self) -> 'SuccessfulArchiveResponse':
        if self.data is None:
            self.validate()
        self.is_update = self.archive_object.entry.archive_id is not None
        url = create_phaidra_update_url(self.archive_object.entry.archive_id)
        response = self._post_to_phaidra(url, self.data)
        return self._handle_phaidra_response(response)

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        return self.push_to_archive()

    def _post_to_phaidra(self, url, data: dict):
        """

        :param url:
        :param data:
        :return:
        """
        serialized_data = json.dumps(data)
        logging.debug(f'Post to phaidra with metadata {data}')
        try:
            response = requests.post(
                url, files={'metadata': serialized_data}, auth=(credentials.get('USER'), credentials.get('PWD'))
            )
            return response
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
        if self.is_update:
            if any([alert['type'] != 'success' for alert in data['alerts']]):
                raise RuntimeError(f'Phaidra returned with response {response} and content {response.content}')
            return self.archive_object.entry.archive_id
        else:
            return data['pid']

    def _update_entry_archival_success_in_db(self, pid: str):
        self.archive_object.entry.archive_id = pid
        self.archive_object.entry.archive_URI = urljoin(settings.ARCHIVE_URIS['IDENTIFIER_BASE'], pid)
        now = timezone.now()
        self.archive_object.entry.archive_date = now
        self.archive_object.entry.date_changed = now
        self.archive_object.entry.save(update_fields=['archive_URI', 'archive_id', 'archive_date', 'date_changed'])

    def _create_user_feedback(self, pid: str):
        return SuccessfulArchiveResponse(
            modification_type=ModificationType.updated if self.is_update else ModificationType.created,
            object_description=pid,
            service='PHAIDRA',
        )

    def _translate_data(self, entry: 'Entry') -> Dict:
        return self.translator.translate_data(entry)

    def _translate_errors(self, errors: Dict) -> Dict:
        return self.translator.translate_errors(errors)

    @property
    def schema(self) -> 'PhaidraMetaData':
        if self._schema is None:
            self._schema = PhaidraMetaData()
        return self._schema

    @property
    def translator(self) -> 'PhaidraMetaDataTranslator':
        if self._translator is None:
            self._translator = PhaidraMetaDataTranslator()
        return self._translator


class ThesisMetadataArchiver(DefaultMetadataArchiver):
    translator_class = PhaidraThesisMetaDataTranslator
    base_schema_class = PhaidraThesisContainer

    def __init__(self, archive_object: 'ArchiveObject'):
        super().__init__(archive_object)
        self._concepts_mapper = None

    @property
    def concepts_mapper(self) -> 'BidirectionalConceptsMapper':
        if self._concepts_mapper is None:
            self._concepts_mapper = BidirectionalConceptsMapper.from_entry(entry=self.archive_object.entry)
        return self._concepts_mapper

    @property
    def schema(self) -> 'PhaidraMetaData':
        if self._schema is None:
            self._schema = create_dynamic_phaidra_thesis_meta_data_schema(self.concepts_mapper)
        return self._schema

    @property
    def translator(self) -> 'PhaidraThesisMetaDataTranslator':
        if self._translator is None:
            self._translator = PhaidraThesisMetaDataTranslator()
        return self._translator

    def _translate_data(self, entry: 'Entry') -> Dict:
        return self.translator.translate_data(entry, self.concepts_mapper)

    def _translate_errors(self, errors: Dict) -> Dict:
        return self.translator.translate_errors(errors, self.concepts_mapper)
