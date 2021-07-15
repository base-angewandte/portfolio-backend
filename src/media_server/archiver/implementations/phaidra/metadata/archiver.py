from abc import ABC
from typing import TYPE_CHECKING, Dict, Optional

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.default.schemas import (
    _PhaidraMetaData,
    get_phaidra_meta_data_schema_with_dynamic_fields,
)

from ....interface.responses import SuccessfulArchiveResponse
from .mappings.contributormapping import BidirectionalConceptsMapper
from .thesis.datatranslation import PhaidraThesisMetaDataTranslator
from .thesis.schemas import _PhaidraThesisMetaDataSchema

if TYPE_CHECKING:
    from ....interface.archiveobject import ArchiveObject

from ....interface.abstractarchiver import AbstractArchiver


class DefaultMetadataArchiver(AbstractArchiver):
    def push_to_archive(self) -> 'SuccessfulArchiveResponse':
        raise NotImplementedError()

    data: Optional[Dict] = None
    mapper_class = BidirectionalConceptsMapper
    translator_class = PhaidraMetaDataTranslator
    base_schema_class = _PhaidraMetaData

    def __init__(self, archive_object: 'ArchiveObject'):
        super().__init__(archive_object)
        self.data = None

    def validate(self) -> None:
        contributor_role_mapping = self.mapper_class.from_entry(self.archive_object.entry)
        translator = self.translator_class()
        data = translator.translate_data(self.archive_object.entry, contributor_role_mapping)
        schema = get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=contributor_role_mapping, base_schema_class=self.base_schema_class
        )
        result = schema.load(data)
        errors: dict = result.errors
        self.data = result.data
        errors = translator.translate_errors(errors, contributor_role_mapping)
        self.throw_validation_errors(errors)


class ThesisMetadataArchiver(DefaultMetadataArchiver, ABC):

    translator_class = PhaidraThesisMetaDataTranslator
    base_schema_class = _PhaidraThesisMetaDataSchema
