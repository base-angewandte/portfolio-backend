"""Check out src/media_server/archiver/implementations/phaidra/phaidra_tests/te
st_media_metadata.py Checkout
src/media_server/archiver/implementations/phaidra/metadata/schemas.py."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Hashable, List, Optional, Union
from urllib.parse import urlparse

from media_server.archiver.messages.validation import MISSING_DATA_FOR_REQUIRED_FIELD

if TYPE_CHECKING:
    from media_server.models import Entry

from media_server.archiver.implementations.phaidra.abstracts.datatranslation import (
    AbstractDataTranslator,
    AbstractUserUnrelatedDataTranslator,
)


class LanguageNotInTranslationMappingError(NotImplementedError):
    pass


def _convert_two_to_three_letter_language_code(language_code: str) -> str:
    """To do :-) ?!"""
    if len(language_code) == 3:
        return language_code
    language_mapping = {
        'en': 'eng',
        'de': 'deu',
    }
    if language_code in language_mapping:
        return language_mapping[language_code]
    else:
        raise LanguageNotInTranslationMappingError(
            f'Can not translate language code {language_code}, only {set(language_mapping.keys())} are supported'
        )


def _create_type_object(type_: str) -> Dict[str, str]:
    return {'@type': type_}


def _create_value_object(value: str) -> Dict[str, str]:
    return {'@value': value}


def _create_value_language_object(value: str, language: str) -> Dict[str, str]:
    return {**_create_value_object(value), '@language': _convert_two_to_three_letter_language_code(language)}


def _create_value_language_objects_from_label_dict(container: Dict, raise_=False) -> List:
    labels: Dict = container['label']
    value_language_objects = []
    for language, label in labels.items():
        try:
            value_language_object = _create_value_language_object(label, language)
        except LanguageNotInTranslationMappingError as error:
            if raise_:
                raise error
            else:
                continue
        value_language_objects.append(value_language_object)
    return value_language_objects


def create_person_object(source: str, name: str) -> Dict[str, List[Dict[str, str]]]:
    person_object = {
        **_create_type_object('schema:Person'),
        'skos:exactMatch': [],
        'schema:name': [
            {
                **_create_value_object(name),
            }
        ],
    }

    if source is not None:
        person_object['skos:exactMatch'].append(
            {
                '@value': source,
                **_create_type_object('ids:uri'),
            }
        )
    return person_object


class DCTitleTranslator(AbstractDataTranslator):
    """A list of titles, where in our database is only one."""

    def translate_data(self, model: 'Entry') -> List[Dict[str, List[Dict[str, str]]]]:
        title_object = {
            **_create_type_object('bf:Title'),
            'bf:mainTitle': [
                _create_value_language_object(model.title, 'und'),
            ],
        }
        if model.subtitle:
            title_object['bf:subtitle'] = [
                _create_value_language_object(model.subtitle, 'und'),
            ]

        return [
            title_object,
        ]

    def translate_errors(self, errors: Dict[int, Dict]) -> Dict:
        translated_errors = {}
        if errors.__len__() == 0:
            return translated_errors
        if errors.__len__() != 1:
            raise RuntimeError(f'Title array is defined as length 1, not {errors.__len__()}')
        errors = errors[0]
        try:
            translated_errors['title'] = errors['bf:mainTitle'][0]['@value']
        except KeyError:
            pass
        try:
            translated_errors['subtitle'] = errors['bf:subtitle'][0]['@value']
        except KeyError:
            pass

        return translated_errors


class EdmHasTypeTranslator(AbstractDataTranslator):
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
        if not model.type:
            return []
        return [
            {
                **_create_type_object('skos:Concept'),
                'skos:prefLabel': self._translate_skos_prefLabel(model),
                'skos:exactMatch': self._translate_skos_exactMatch(model),
            },
        ]

    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        """Minimum length is 1 on phaidra site, on ours only missing.

        :param errors:
        :return:
        """
        if errors:
            return {
                'type': [
                    MISSING_DATA_FOR_REQUIRED_FIELD,
                ]
            }
        else:
            return {}

    def _translate_skos_prefLabel(self, model: 'Entry') -> List[Dict[str, str]]:
        if 'label' not in model.type:
            return []
        type_labels: Dict = model.type['label']
        return [
            _create_value_language_object(language=language, value=label) for language, label in type_labels.items()
        ]

    def _translate_skos_exactMatch(self, model: 'Entry') -> List[str]:
        if 'source' not in model.type:
            return []
        return [
            model.type['source'],
        ]


class GenericSkosConceptTranslator(AbstractUserUnrelatedDataTranslator):
    """Currently used on dcterms:subject, rdau:P60048, dce:format."""

    raise_on_not_found_error: bool
    entry_attribute: str
    json_keys: List[Hashable]

    def __init__(
        self, entry_attribute: str, json_keys: Optional[List[Hashable]] = None, raise_on_not_found_error: bool = False
    ):
        self.entry_attribute = entry_attribute
        self.raise_on_not_found_error = raise_on_not_found_error
        self.json_keys = [] if json_keys is None else json_keys

    def translate_data(self, model: 'Entry') -> List[Dict]:
        data_of_interest = self._get_data_of_interest(model)
        if data_of_interest.__len__() == 0:
            return data_of_interest
        return self._translate(data_of_interest)

    def _get_data_of_interest(self, model: 'Entry') -> List[Dict]:
        data_of_interest: Dict = getattr(model, self.entry_attribute)
        if data_of_interest is None:
            if self.raise_on_not_found_error:
                raise AttributeError(f'Attribute Entry.{self.entry_attribute} is empty')
            else:
                return []
        for key in self.json_keys:
            try:
                data_of_interest = data_of_interest[key]
            except KeyError as error:
                if self.raise_on_not_found_error:
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
            if 'source' in datum
        ]


class BfNoteTranslator(AbstractUserUnrelatedDataTranslator):
    def translate_data(self, model: 'Entry') -> List[Dict]:
        # Bail early, if this field is NULL
        if model.texts is None:
            return []
        texts = self._filter_not_abstract_text_type(model)
        translated = []
        for text in texts:
            translated_text: Dict[str, Union[str, List[Dict]]] = _create_type_object(
                'bf:Summary' if 'type' in text else 'bf:Note'
            )
            try:
                translated_text['skos:prefLabel'] = self._get_data_from_skos_prefLabel_from_text_type(text)
            except LanguageNotInTranslationMappingError:
                continue  # if not available in target, do not translate
            translated.append(translated_text)
        return translated

    def _get_data_from_skos_prefLabel_from_text_type(self, text: Dict) -> List:
        if 'data' not in text:
            return []
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

    def _filter_not_abstract_text_type(self, model: 'Entry') -> List[Dict]:
        abstract_source = 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract'
        return [
            text
            for text in model.texts
            if ('type' not in text) or (('source' in text['type']) and text['type']['source'] == abstract_source)
        ]


class GenericStaticPersonTranslator(AbstractUserUnrelatedDataTranslator):
    role_uri: str
    primary_level_data_key: str

    def __init__(self, primary_level_data_key: Optional[str], role_uri: str):
        """

        :param primary_level_data_key: The key to look for persons in Entry.data[key]
        :param role_uri:  Look for persons with this role in Entry.data[contributors]
        """
        self.role_uri = role_uri
        self.primary_level_data_key = primary_level_data_key

    def translate_data(self, model: 'Entry') -> List[Dict[str, List[Dict[str, str]]]]:
        if model.data is None:
            # Bail early on model.data is null, since is nullable
            return []
        first_level_persons = self._get_first_level_persons(model)
        contributors = self._get_contributors(model)
        return first_level_persons + contributors

    def _get_first_level_persons(self, model: 'Entry') -> List[Dict[str, List[Dict[str, str]]]]:
        if self.primary_level_data_key not in model.data:
            return []
        return [
            create_person_object(name=person['label'], source=person['source'])
            for person in model.data[self.primary_level_data_key]
        ]

    def _get_contributors(self, model: 'Entry') -> List[Dict[str, List[Dict[str, str]]]]:
        if 'contributors' not in model.data:
            return []
        contributors = []
        for contributor in model.data['contributors']:
            if 'roles' in contributor:
                for role in contributor['roles']:
                    if role['source'] == self.role_uri:
                        contributors.append(create_person_object(source=role['source'], name=contributor['label']))
        return contributors


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

    _key_translator_mapping: Dict[str, AbstractDataTranslator]

    def __init__(self):
        self._key_translator_mapping = {
            'edm:hasType': EdmHasTypeTranslator(),
            'dce:title': DCTitleTranslator(),
            'dcterms:language': GenericSkosConceptTranslator(
                'data',
                [
                    'language',
                ],
                raise_on_not_found_error=False,
            ),
            'dcterms:subject': GenericSkosConceptTranslator('keywords'),
            'rdau:P60048': GenericSkosConceptTranslator('data', ['material'], raise_on_not_found_error=False),
            'dce:format': GenericSkosConceptTranslator('data', ['format'], raise_on_not_found_error=False),
            'bf:note': BfNoteTranslator(),
            'role:edt': GenericStaticPersonTranslator(
                primary_level_data_key='editors',
                role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/editor',
            ),
            'role:aut': GenericStaticPersonTranslator(
                primary_level_data_key='authors',
                role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author',
            ),
            'role:pbl': GenericStaticPersonTranslator(
                primary_level_data_key='publishers',
                role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/publisher',
            ),
        }

    def translate_data(self, model: 'Entry') -> dict:
        data = self._translate_data(model)
        data = self._wrap_in_container(data)
        return data

    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        errors = self._extract_from_container(errors)
        errors = self._translate_errors(errors)
        return self._filter_errors(errors)

    def _translate_data(self, model: 'Entry') -> Dict:
        return {
            'dcterms:type': self._create_static_dcterms(),
            **{key: translator.translate_data(model) for key, translator in self._key_translator_mapping.items()},
        }

    def _translate_errors(self, errors: Dict) -> Dict:
        translated_errors = {}
        for target_key, translator in self._key_translator_mapping.items():
            if target_key in errors:
                source_errors = translator.translate_errors(errors[target_key])
                translated_errors = self._set_nested_errors(source_errors, translated_errors)
        return translated_errors

    @staticmethod
    def _create_static_dcterms() -> List:
        return [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
            }
        ]

    @classmethod
    def _filter_errors(cls, errors: Dict) -> Dict:
        errors = cls._recursive_filter_errors(errors)
        return {} if errors is None else errors  # keep to level dict

    @classmethod
    def _recursive_filter_errors(cls, errors: Union[Dict, List]) -> Optional[Union[Dict, List]]:
        """Since we use marshmallow, we assume objects container either nested
        objects or lists of errors.

        :param errors:
        :return:
        """
        if errors.__class__ is dict:
            filtered_errors = {}
            for key, value in errors.items():
                filtered_value = cls._recursive_filter_errors(value)
                if filtered_value is not None:
                    filtered_errors[key] = filtered_value

        elif errors.__class__ is list:
            filtered_errors = []
            for value in errors:
                filtered_value = cls._recursive_filter_errors(value)
                if filtered_value is not None:
                    filtered_errors.append(filtered_value)
        else:
            return errors  # leave node
        return filtered_errors if filtered_errors else None

    def _set_nested_errors(self, source_errors: Dict, translated_errors: Dict) -> Dict:
        for key, value in source_errors.items():
            # it is the error message, set it
            if value.__class__ is list:
                if key not in translated_errors:
                    translated_errors[key] = value
                else:
                    if translated_errors[key].__class__ is list:
                        translated_errors[key] += value
                    else:
                        raise TypeError(f'Cant add error {value} on errors{translated_errors}')
            else:
                # go one step beyond
                if key not in translated_errors:
                    translated_errors[key] = {}
                sub_errors = translated_errors[key]
                translated_errors[key] = self._set_nested_errors(value, sub_errors)
        return translated_errors

    def _wrap_in_container(self, data: Any) -> Dict:
        return {
            'metadata': {
                'json-ld': data,
            }
        }

    def _extract_from_container(self, data: Dict) -> Any:
        try:
            return data['metadata']['json-ld']
        except KeyError:
            return {}
