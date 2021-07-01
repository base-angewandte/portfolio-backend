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
            'rdau:P60048': self.get_type_match_label_list(
                model,
                [
                    'material',
                ],
            ),
            'dce:format': self.get_type_match_label_list(
                model,
                [
                    'format',
                ],
            ),
            'bf:note': self.get_get_bf_note(model),
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
                'skos:prefLabel': self.get_skos_prefLabel_from_entry(model),
                'skos:exactMatch': self.get_skos_exactMatch(model),
            }
        ]

    def get_skos_prefLabel_from_entry(self, model: 'Entry') -> List:
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
        return [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': [keyword['source']] if 'source' in keyword else [],
                'skos:prefLabel': self.get_skos_prefLabel_from_label_items_dict(keyword),
            }
            for keyword in model.keywords
        ]

    def get_skos_prefLabel_from_label_items_dict(self, container: Dict) -> List:
        try:
            labels: Dict = container['label']['items']
            return [
                {
                    '@value': label,
                    '@language': language,
                }
                for language, label in labels.items()
            ]
        except KeyError:
            return []

    def get_type_match_label_list(self, model: 'Entry', data_keys: List[str]) -> List:
        try:
            items = model.data
            for data_key in data_keys:
                items = items[data_key]
        except KeyError:
            return []

        return [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': [item['source']] if 'source' in item else [],
                'skos:prefLabel': self.get_skos_prefLabel_from_label_items_dict(item),
            }
            for item in items
        ]

    def get_get_bf_note(self, model: 'Entry') -> List:
        abstract_source = 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract'
        text: Dict
        texts = [
            text
            for text in model.texts
            if ('type' not in text) or (('source' in text['type']) and text['type']['source'] == abstract_source)
        ]
        return [
            {
                '@type': 'bf:Summary' if 'type' in text else 'bf:Note',
                'skos:prefLabel': self.get_skos_prefLabel_from_text(text),
            }
            for text in texts
        ]

    def get_skos_prefLabel_from_text(self, text: Dict) -> List:
        try:
            text_data = text['data']
        except KeyError:
            return []
        return [
            {'@value': text_datum['text'], '@language': text_datum['language']['source']}
            for text_datum in text_data
            if ('text' in text_datum) and ('language' in text_datum) and ('source' in text_datum['language'])
        ]
