from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from media_server.models import Entry
    from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
        BidirectionalConceptsMapper,
    )

from media_server.archiver.implementations.phaidra.abstracts.datatranslation import AbstractDataTranslator


class PhaidraMetaDataTranslator(AbstractDataTranslator):
    def translate_data(self, model: 'Entry', contributor_role_mapping: 'BidirectionalConceptsMapper' = None) -> dict:
        data_with_static_structure = self._get_data_with_static_structure(model)
        data_with_dynamic_structure = self._get_data_with_dynamic_structure(model, contributor_role_mapping)
        return self._merge(data_with_static_structure, data_with_dynamic_structure)

    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        raise NotImplementedError()

    def _get_data_with_static_structure(self, model: 'Entry') -> Dict:
        return {
            'dcterms:type': self._get_dcterms_type(),
            'edm:hasType': self._get_edm_hasType(model),
            'dce:title': self.get_dc_title(model),
            'dcterms:subject': self._get_dcterms_subject(model),
            'rdau:P60048': self._get_type_match_label_list(
                model,
                [
                    'material',
                ],
            ),
            'dce:format': self._get_type_match_label_list(
                model,
                [
                    'format',
                ],
            ),
            'bf:note': self._get_get_bf_note(model),
            'role:edt': self._get_role_by(model, 'editors', 'http://base.uni-ak.ac.at/portfolio/vocabulary/editor'),
            'role:aut': self._get_role_by(model, 'authors', 'http://base.uni-ak.ac.at/portfolio/vocabulary/author'),
            'role:pbl': self._get_role_by(
                model, 'role:pbl', 'http://base.uni-ak.ac.at/portfolio/vocabulary/publisher'
            ),
        }

    def _get_dcterms_type(self) -> List:
        return [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
            }
        ]

    def _get_edm_hasType(self, model: 'Entry') -> List:
        return [
            {
                '@type': 'skos:Concept',
                'skos:prefLabel': self._get_skos_prefLabel_from_entry(model),
                'skos:exactMatch': self._get_skos_exactMatch(model),
            }
        ]

    def _get_skos_prefLabel_from_entry(self, model: 'Entry') -> List:
        try:
            items: Dict = model.type['label']['items']
        except KeyError:
            return []
        return [{'@value': label, '@language': language} for language, label in items.items()]

    def _get_skos_exactMatch(self, model: 'Entry') -> List:
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

    def _get_dcterms_subject(self, model: 'Entry') -> List:
        return [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': [keyword['source']] if 'source' in keyword else [],
                'skos:prefLabel': self._get_skos_prefLabel_from_label_items_dict(keyword),
            }
            for keyword in model.keywords
        ]

    def _get_skos_prefLabel_from_label_items_dict(self, container: Dict) -> List:
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

    def _get_type_match_label_list(self, model: 'Entry', data_keys: List[str]) -> List:
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
                'skos:prefLabel': self._get_skos_prefLabel_from_label_items_dict(item),
            }
            for item in items
        ]

    def _get_get_bf_note(self, model: 'Entry') -> List:
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
                'skos:prefLabel': self._get_skos_prefLabel_from_text(text),
            }
            for text in texts
        ]

    def _get_skos_prefLabel_from_text(self, text: Dict) -> List:
        try:
            text_data = text['data']
        except KeyError:
            return []
        return [
            {'@value': text_datum['text'], '@language': text_datum['language']['source']}
            for text_datum in text_data
            if ('text' in text_datum) and ('language' in text_datum) and ('source' in text_datum['language'])
        ]

    def _get_role_by(self, model: 'Entry', main_level: str, role_uri: str) -> List:
        has_main_level_persons = main_level in model.data
        has_contributors = 'contributors' in model.data
        if not has_main_level_persons and not has_contributors:
            return []

        all_persons = []

        if has_main_level_persons:
            for person in model.data[main_level]:
                if ('source' in person) and ('label' in person):
                    all_persons.append(
                        {
                            'skos:exactMatch': [{'@value': person['source'], '@type': 'ids:uri'}],
                            'schema:name': [
                                {
                                    '@value': person['label'],
                                }
                            ],
                            '@type': 'schema:Person',
                        }
                    )

        if has_contributors:
            contributors = model.data['contributors']
            for contributor in contributors:
                if 'roles' in contributor:
                    for role in contributor['roles']:
                        if ('source' in role) and (role['source'] == role_uri):
                            all_persons.append(
                                {
                                    'skos:exactMatch': [{'@value': role['source'], '@type': 'ids:uri'}],
                                    'schema:name': [
                                        {
                                            '@value': contributor['label'],
                                        }
                                    ],
                                    '@type': 'schema:Person',
                                }
                            )

        return all_persons

    def _get_data_with_dynamic_structure(
        self, model: 'Entry', contributor_role_mapping: 'BidirectionalConceptsMapper'
    ):
        data_with_dynamic_structure = defaultdict(list)
        if 'contributors' not in model.data:
            return data_with_dynamic_structure
        contributors: List[Dict] = model.data['contributors']
        for contributor in contributors:
            if ('roles' not in contributor) or ('source' not in contributor) or ('label' not in contributor):
                continue
            for role in contributor['roles']:
                if 'source' not in role:
                    continue
                phaidra_roles = contributor_role_mapping.get_owl_sameAs_from_uri(role['source'])
                for phaidra_role in phaidra_roles:
                    data_with_dynamic_structure[phaidra_role].append(
                        {
                            'skos:exactMatch': [{'@value': contributor['source'], '@type': 'ids:uri'}],
                            'schema:name': [{'@value': contributor['label']}],
                            '@type': 'schema:Person',
                        },
                    )
            return data_with_dynamic_structure

    def _merge(self, data_with_static_structure: dict, data_with_dynamic_structure: dict):
        for key, value in data_with_dynamic_structure.items():
            if key not in data_with_static_structure:
                data_with_static_structure[key] = value
            elif data_with_static_structure[key].__class__ is list and value.__class__ is list:
                data_with_static_structure[key] += value
            else:
                pass  # All we do right now
        return data_with_static_structure
