from typing import Dict, List, Optional, Union

from marshmallow import fields

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import (
    BfNoteTranslator,
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


class ResponsiveBfNoteTranslator(BfNoteTranslator):
    def translate_errors(self, errors: Union[List[str], Dict]) -> Dict[str, List[str]]:
        if errors.__class__ is list:
            return {'texts': errors}
        else:
            super().translate_errors(errors)


class ResponsiveGenericStaticPersonTranslator(GenericStaticPersonTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: Union[Dict, List]) -> Dict:
        """Since all of this errors are on schema level, we just to add the top
        keys.

        :param errors:
        :return:
        """
        if not errors:
            return {}
        return {'data': {self.primary_level_data_key: errors}}


class AdvisorSupervisorTranslator(GenericStaticPersonTranslator):
    def __init__(self):
        super().__init__(None, 'http://base.uni-ak.ac.at/portfolio/vocabulary/advisor')

    def translate_errors(self, errors: Union[Dict, List]) -> Dict:
        """Empty or missing: Always send the same message.

        :param errors:
        :return:
        """
        if not errors:
            return {}
        return {
            'data': {
                'contributors': [
                    'At least one contributor has to have the role advisor.',
                ],
            }
        }


class PhaidraThesisMetaDataTranslator(PhaidraMetaDataTranslator):
    def __init__(self):
        super().__init__()

        self._static_key_translator_mapping['role:aut'] = ResponsiveGenericStaticPersonTranslator(
            primary_level_data_key='authors',
            role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author',
        )

        self._static_key_translator_mapping['dcterms:language'] = ResponsiveGenericSkosConceptTranslator(
            'data',
            [
                'language',
            ],
            raise_on_not_found_error=False,
        )

        self._static_key_translator_mapping['role:supervisor'] = AdvisorSupervisorTranslator()
        self._static_key_translator_mapping['bf:note'] = ResponsiveBfNoteTranslator()
