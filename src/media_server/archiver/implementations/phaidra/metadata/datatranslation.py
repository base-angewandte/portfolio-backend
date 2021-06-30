from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from media_server.models import Entry

from media_server.archiver.implementations.phaidra.abstracts.datatranslation import AbstractDataTranslator


class PhaidraMetaDataTranslator(AbstractDataTranslator):
    def translate_data(self, model: 'Entry') -> dict:
        return {
            'dcterms:type': self.get_dcterms_type(),
            'edm:hasType': self.get_edm_hasType(model),
            'dce:title': self.get_dc_title(model),
            'dcterms:subject': self.get_dcterms_subject(model),
        }

    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        raise NotImplementedError()

    def get_dcterms_type(self) -> List:
        return [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
            }
        ]

    def get_edm_hasType(self, model: 'Entry') -> List:
        return [
            {
                '@type': 'skos:Concept',
                'skos:prefLabel': self.get_skos_prefLabel(model),
                'skos:exactMatch': self.get_skos_exactMatch(model),
            }
        ]

    def get_skos_prefLabel(self, model: 'Entry') -> List:
        try:
            items: Dict = model.type['label']['items']
        except KeyError:
            return []
        return [{'@value': label, '@language': language} for language, label in items.items()]

    def get_skos_exactMatch(self, model: 'Entry') -> List:
        try:
            return [
                model.type['source'],
            ]
        except KeyError:
            return []

    def get_dc_title(self, model: 'Entry') -> List:
        return [
            {
                '@type': 'bf:Title',
                'bf:mainTitle': {
                    '@value': model.title,
                    '@language': 'und',
                },
                'bf:subtitle': {
                    '@value': model.subtitle,
                    '@language': 'und',
                },
            }
        ]

    def get_dcterms_subject(self, model: 'Entry') -> List:
        raise NotImplementedError()
