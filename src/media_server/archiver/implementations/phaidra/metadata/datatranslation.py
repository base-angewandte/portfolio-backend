"""Check out src/media_server/archiver/implementations/phaidra/phaidra_tests/te
st_media_metadata.py Checkout
src/media_server/archiver/implementations/phaidra/metadata/schemas.py."""
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Hashable, List, Optional
from urllib.parse import urlparse

from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import get_phaidra_role_code

if TYPE_CHECKING:
    from media_server.models import Entry
    from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
        BidirectionalConceptsMapper,
    )

from media_server.archiver.implementations.phaidra.abstracts.datatranslation import (
    AbstractDataTranslator,
    AbstractUserUnrelatedDataTranslator,
)


def _convert_two_to_three_letter_language_code(language_code: str) -> str:
    """To do :-) ?!"""
    if len(language_code) == 3:
        return language_code
    return {
        'en': 'eng',
        'de': 'deu',
    }[language_code]


def _create_type_object(type_: str) -> Dict[str, str]:
    return {'@type': type_}


def _create_value_object(value: str) -> Dict[str, str]:
    return {'@value': value}


def _create_value_language_object(value: str, language: str) -> Dict[str, str]:
    return {**_create_value_object(value), '@language': _convert_two_to_three_letter_language_code(language)}


def _create_value_language_objects_from_label_dict(container: Dict) -> List:
    labels: Dict = container['label']
    return [_create_value_language_object(label, language) for language, label in labels.items()]


class DCTitleTranslator(AbstractDataTranslator):
    """A list of titles, where in our database is only one."""

    def translate_data(self, model: 'Entry') -> List[Dict[str, List[Dict[str, str]]]]:
        title_container = _create_type_object('bf:Title')
        if model.title:
            title_container['bf:mainTitle'] = [
                _create_value_language_object(model.title, 'und'),
            ]
        if model.subtitle:
            title_container['bf:subtitle'] = [
                _create_value_language_object(model.subtitle, 'und'),
            ]
        return [title_container]

    def translate_errors(self, errors: List[Dict]) -> Dict:
        translated_errors = {}
        if errors.__len__() == 0:
            return translated_errors
        if errors.__len__() != 1:
            raise RuntimeError(f'Title array is defined as length 1, not {errors.__len__()}')
        errors = errors.pop()
        try:
            translated_errors['title'] = errors['bf:mainTitle'][0]['@value']
        except KeyError:
            pass
        try:
            translated_errors['subtitle'] = errors['bf:subtitle'][0]['@value']
        except KeyError:
            pass

        return translated_errors


class EdmHasTypeTranslator(AbstractUserUnrelatedDataTranslator):
    def translate_data(self, model: 'Entry') -> List[Dict]:
        """
        For Example
        ```
        model.type = {
            "label": {
                "de": "Artikel",
                "en": "article"
            },
            "source": "http://base.uni-ak.ac.at/portfolio/taxonomy/article"
        }
        :param model:
        :return:
        """
        return [
            {
                **_create_type_object('skos:Concept'),
                'skos:prefLabel': self._translate_skos_prefLabel(model),
                'skos:exactMatch': self._translate_skos_exactMatch(model),
            },
        ]

    def _translate_skos_prefLabel(self, model: 'Entry') -> List[Dict[str, str]]:
        try:
            type_labels: Dict = model.type['label']
        except KeyError:
            raise RuntimeError(f"Expected model.type['label'], but type only contains {model.type.keys()}")
        except TypeError:
            raise RuntimeError(f'Expected model.type to be dict, but got {model.type.__class__}')
        return [
            _create_value_language_object(language=language, value=label) for language, label in type_labels.items()
        ]

    def _translate_skos_exactMatch(self, model: 'Entry') -> List[str]:
        try:
            return [
                model.type['source'],
            ]
        except KeyError:
            raise RuntimeError(f"Expected model.type['source'], but type only contains {model.type.keys()}")
        except TypeError:
            raise RuntimeError(f'Expected model.type to be dict, but got {model.type.__class__}')


class GenericSkosConceptTranslator(AbstractUserUnrelatedDataTranslator):
    """Currently used on dcterms:subject, rdau:P60048, dce:format."""

    raise_on_key_error: bool
    entry_attribute: str
    json_keys: List[Hashable]

    def __init__(
        self, entry_attribute: str, json_keys: Optional[List[Hashable]] = None, raise_on_key_error: bool = False
    ):
        self.entry_attribute = entry_attribute
        self.raise_on_key_error = raise_on_key_error
        self.json_keys = [] if json_keys is None else json_keys

    def translate_data(self, model: 'Entry') -> List[Dict]:
        data_of_interest = self._get_data_of_interest(model)
        if data_of_interest.__len__() == 0:
            return data_of_interest
        return self._translate(data_of_interest)

    def _get_data_of_interest(self, model: 'Entry') -> List[Dict]:
        data_of_interest: Dict = getattr(model, self.entry_attribute)
        for key in self.json_keys:
            try:
                data_of_interest = data_of_interest[key]
            except KeyError as error:
                if self.raise_on_key_error:
                    raise error
                else:
                    return []
        data_of_interest: List[Dict]
        return data_of_interest

    def _translate(self, data_of_interest: List[Dict]) -> List[Dict]:
        return [
            {
                **_create_type_object('skos:Concept'),
                'skos:exactMatch': [datum['source']],
                'skos:prefLabel': _create_value_language_objects_from_label_dict(datum),
            }
            for datum in data_of_interest
        ]


class BfNoteTranslator(AbstractUserUnrelatedDataTranslator):
    def translate_data(self, model: 'Entry') -> List[Dict]:
        abstract_source = 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract'
        text: Dict
        texts = [
            text
            for text in model.texts
            if ('type' not in text) or (('source' in text['type']) and text['type']['source'] == abstract_source)
        ]
        return [
            {
                **_create_type_object('bf:Summary' if 'type' in text else 'bf:Note'),
                'skos:prefLabel': self._get_data_from_skos_prefLabel_from_text_type(text),
            }
            for text in texts
        ]

    def _get_data_from_skos_prefLabel_from_text_type(self, text: Dict) -> List:
        text_data = text['data']
        return [
            self._create_value_language_object(text_datum)
            for text_datum in text_data
            if ('text' in text_datum) and ('language' in text_datum) and ('source' in text_datum['language'])
        ]

    def _create_value_language_object(self, text_datum: Dict) -> Dict:
        source = text_datum['language']['source']
        parsed_source = urlparse(source)
        parsed_path = Path(parsed_source.path)
        return _create_value_language_object(value=text_datum['text'], language=parsed_path.name)


class PhaidraMetaDataTranslator(AbstractDataTranslator):
    """This module translates data from Entry(.data) to phaidra metadata format
    and from the error messages of the validation process back to Entry(.data).
    See .schemas.

    Data and error translation is done in one class, because they are very similar in key/data structure. However this
    class is quite big: It could and should me split into more classes, which also would ease creation of endpoints for
    just parts of the data structure.

    Also a lot of the abstract workflow is quite repetitive. An abstraction of the workflow into simple imperative
    statements, that just describe the data structure would be advisable. At the current timeline of the project
    this seems to make too much overhead.

    The following approach was taken to "structure": The target structure is split into smaller (nested) components.
    Each of this components is filled by a method. The ones that take data from source and translate it to the target
    are prefixed _get_data_for_<component>. The ones that take error messages from the validation process and
    translate them back into the source data model, are prefixed _get_errors_from_<component>. These methods are
    ordered pairwise.
    """

    dc_title_translator: DCTitleTranslator

    def __init__(self):
        self.dc_title_translator = DCTitleTranslator()
        self.edm_has_type_translator = EdmHasTypeTranslator()
        self.dcterms_subject_translator = GenericSkosConceptTranslator('keywords')
        self.rdau_P60048_translator = GenericSkosConceptTranslator('data', ['material'], raise_on_key_error=False)
        self.dce_format_translator = GenericSkosConceptTranslator('data', ['format'], raise_on_key_error=False)
        self.bf_note_translator = BfNoteTranslator()

    def translate_data(self, model: 'Entry', contributor_role_mapping: 'BidirectionalConceptsMapper' = None) -> dict:
        data_with_static_structure = self._get_data_with_static_structure(model)
        data_with_dynamic_structure = self._get_data_with_dynamic_structure(model, contributor_role_mapping)
        return self._merge(data_with_static_structure, data_with_dynamic_structure)

    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        raise NotImplementedError()

    def _get_data_with_static_structure(self, model: 'Entry') -> Dict:
        return {
            'dcterms:type': self._create_static_dcterms(),
            'edm:hasType': self.edm_has_type_translator.translate_data(model),
            'dce:title': self.dc_title_translator.translate_data(model),
            'dcterms:subject': self.dcterms_subject_translator.translate_data(model),
            'rdau:P60048': self.rdau_P60048_translator.translate_data(model),
            'dce:format': self.dce_format_translator.translate_data(model),
            'bf:note': self.bf_note_translator.translate_data(model),
            'role:edt': self._get_data_from_role_by(
                model, 'editors', 'http://base.uni-ak.ac.at/portfolio/vocabulary/editor'
            ),
            'role:aut': self._get_data_from_role_by(
                model, 'authors', 'http://base.uni-ak.ac.at/portfolio/vocabulary/author'
            ),
            'role:pbl': self._get_data_from_role_by(
                model, 'role:pbl', 'http://base.uni-ak.ac.at/portfolio/vocabulary/publisher'
            ),
        }

    @staticmethod
    def _create_static_dcterms() -> List:
        return [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
            }
        ]

    def _get_data_from_role_by(self, model: 'Entry', main_level: str, role_uri: str) -> List:
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
                    data_with_dynamic_structure[get_phaidra_role_code(phaidra_role)].append(
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
