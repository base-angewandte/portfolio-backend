from typing import Dict, List, Optional, Union

from marshmallow import fields

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import (
    GenericSkosConceptTranslator,
    GenericStaticPersonTranslator,
    PhaidraMetaDataTranslator,
)


class ResponsiveGenericSkosConceptTranslator(GenericSkosConceptTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: Optional[Union[List[Dict], Dict]]) -> Dict:
        if not errors:
            return {}
        translated_errors = {}
        translated_errors = self.set_nested(
            keys=[self.entry_attribute, *self.json_keys],
            value=[
                fields.Field.default_error_messages['required'],
            ],
            target=translated_errors,
        )
        return translated_errors


class ResponsiveGenericStaticPersonTranslator(GenericStaticPersonTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: List) -> Dict:
        """Since all of this errors are on schema level, we just to add the top
        keys.

        :param errors:
        :return:
        """
        if not errors:
            return {}
        return {'data': {self.primary_level_data_key: errors}}


class PhaidraThesisMetaDataTranslator(PhaidraMetaDataTranslator):
    def __init__(self):

        super().__init__()

        parent_author_translator: 'GenericStaticPersonTranslator' = self._static_key_translator_mapping['role:aut']
        self._static_key_translator_mapping['role:aut'] = ResponsiveGenericStaticPersonTranslator(
            primary_level_data_key=parent_author_translator.primary_level_data_key,
            role_uri=parent_author_translator.role_uri,
        )

        parent_language_translator: 'GenericSkosConceptTranslator' = self._static_key_translator_mapping[
            'dcterms:language'
        ]
        self._static_key_translator_mapping['dcterms:language'] = ResponsiveGenericSkosConceptTranslator(
            entry_attribute=parent_language_translator.entry_attribute,
            json_keys=parent_language_translator.json_keys,
            raise_on_not_found_error=parent_language_translator.raise_on_not_found_error,
        )
