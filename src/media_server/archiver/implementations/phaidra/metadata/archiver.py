from typing import TYPE_CHECKING, Dict, Optional

from .datatranslation import PhaidraMetaDataTranslator
from .mappings.contributormapping import BidirectionalConceptsMapper
from .schemas import get_phaidra_meta_data_schema_with_dynamic_fields

if TYPE_CHECKING:
    from ....interface.archiveobject import ArchiveObject
from ....interface.abstractarchiver import AbstractArchiver


class DefaultMetadataArchiver(AbstractArchiver):

    data: Optional[Dict] = None

    def __init__(self, archive_object: 'ArchiveObject'):
        super().__init__(archive_object)
        self.data = None

    def validate(self) -> None:
        contributor_role_mapping = BidirectionalConceptsMapper.from_entry(self.archive_object.entry)
        translator = PhaidraMetaDataTranslator()
        data = translator.translate_data(self.archive_object.entry, contributor_role_mapping)
        schema = get_phaidra_meta_data_schema_with_dynamic_fields(contributor_role_mapping)
        result = schema.load(data)
        errors: dict = result.errors
        self.data = result.data
        self.throw_validation_errors(translator.translate_errors(errors))


class ThesisMetadataArchiver(AbstractArchiver):
    pass
