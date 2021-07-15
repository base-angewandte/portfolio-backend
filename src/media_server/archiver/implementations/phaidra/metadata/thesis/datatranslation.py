from typing import Dict, List, Optional, Union

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import (
    GenericStaticPersonTranslator,
    PhaidraMetaDataTranslator,
)


class ResponsiveGenericStaticPersonTranslator(GenericStaticPersonTranslator):
    """Implement basic error feedback."""

    def translate_errors(self, errors: Optional[Union[List[Dict], Dict]]) -> Dict:
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
        parent_auth_translator: 'GenericStaticPersonTranslator' = self._static_key_translator_mapping['role:aut']
        self._static_key_translator_mapping['role:aut'] = ResponsiveGenericStaticPersonTranslator(
            primary_level_data_key=parent_auth_translator.primary_level_data_key,
            role_uri=parent_auth_translator.role_uri,
        )
