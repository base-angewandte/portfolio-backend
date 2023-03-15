from __future__ import annotations

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import (
    BfNoteTranslator,
    GenericSkosConceptTranslator,
    GenericStaticPersonTranslator,
    PhaidraMetaDataTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    BidirectionalConceptsMapper,
)


class ResponsiveGenericSkosConceptTranslator(GenericSkosConceptTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: list[dict] | dict | None) -> dict:
        if not errors:
            return {}
        translated_errors = {}
        translated_errors = self.set_nested(
            keys=[self.entry_attribute, *self.json_keys],
            value=errors,
            target=translated_errors,
        )
        return translated_errors


class ResponsiveBfNoteTranslator(BfNoteTranslator):
    def translate_errors(self, errors: list[str] | dict) -> dict[str, list[str]]:
        if errors.__class__ is list:
            return {'texts': errors}
        else:
            super().translate_errors(errors)


class ResponsiveGenericStaticPersonTranslator(GenericStaticPersonTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: dict | list) -> dict:
        """Since all of this errors are on schema level, we just to add the top
        keys.

        :param errors:
        :return:
        """
        if not errors:
            return {}
        return {'data': {self.primary_level_data_key: errors}}


class PhaidraThesisMetaDataTranslator(PhaidraMetaDataTranslator):
    def __init__(self, mapping: BidirectionalConceptsMapper):
        super().__init__(mapping)

        self._key_translator_mapping['role:aut'] = ResponsiveGenericStaticPersonTranslator(
            primary_level_data_key='authors',
            role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author',
        )

        self._key_translator_mapping['dcterms:language'] = ResponsiveGenericSkosConceptTranslator(
            'data',
            [
                'language',
            ],
            raise_on_not_found_error=False,
        )

        self._key_translator_mapping['bf:note'] = ResponsiveBfNoteTranslator()
