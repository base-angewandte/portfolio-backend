from copy import deepcopy
from typing import TYPE_CHECKING, Dict, List, Optional

from media_server.archiver.implementations.phaidra.metadata.archiver import (
    DefaultMetadataArchiver,
    ThesisMetadataArchiver,
)
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import (
    PhaidraThesisMetaDataTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import _PhaidraThesisMetaDataSchema
from media_server.archiver.interface.archiveobject import ArchiveObject
from media_server.archiver.messages.validation import MISSING_DATA_FOR_REQUIRED_FIELD

if TYPE_CHECKING:
    from media_server.archiver.implementations.phaidra.main import PhaidraArchiver

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import Entry
from media_server.archiver.controller.default import DefaultArchiveController
from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import (
    BfNoteTranslator,
    DCTitleTranslator,
    EdmHasTypeTranslator,
    GenericSkosConceptTranslator,
    GenericStaticPersonTranslator,
    PhaidraMetaDataTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.default.schemas import (
    DceTitleSchema,
    PersonSchema,
    SkosConceptSchema,
    TypeLabelSchema,
    _PhaidraMetaData,
    get_phaidra_meta_data_schema_with_dynamic_fields,
)
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    BidirectionalConceptsMapper,
)
from media_server.archiver.implementations.phaidra.phaidra_tests.test_media_metadata.test_thesis.utillities import (
    ModelProvider,
)
from media_server.archiver.interface.exceptions import InternalValidationError


class MetaDataTitle(TestCase):
    """
    "The entry must have a title."

    ```
    "dce:title": [{
        "@type": "bf:Title",
        "bf:mainTitle": [{
            "@value": "{{entry.title}}",
            "@language": "und"
        }],
        "bf:subtitle": [{
            "@value": "{{entry.subtitle}}",
            "@language": "und"
        }]
    }],
    ```
    """

    _title = 'Phaedra'
    _subtitle = 'Hippolytus'

    def test_only_title_data_flow(self):
        entry = Entry(title=self._title)
        phaidra_data = self._only_title_data_transformation(entry)
        self.assertIs(phaidra_data.__class__, list)  # detailed test in _method
        phaidra_errors = self._only_title_validation(phaidra_data)
        self.assertEqual(
            phaidra_errors,
            {
                0: {},
            },
        )
        portfolio_errors = self._only_title_error_transformation(phaidra_errors)
        self.assertEqual(portfolio_errors, {})

    def test_only_subtitle_data_flow(self):
        entry = Entry(subtitle=self._subtitle)
        phaidra_data = self._only_subtitle_data_transformation(entry)
        self.assertIs(phaidra_data.__class__, list)  # detailed test in _method
        phaidra_errors = self._only_subtitle_validation(phaidra_data)
        self.assertEqual(len(phaidra_errors), 1)
        self.assertIs(phaidra_errors.__class__, dict)
        portfolio_errors = self._only_subtitle_error_transformation(phaidra_errors)
        # title is no error, because default empty string
        self.assertEqual(len(portfolio_errors), 0)  # details in _method

    def _only_title_data_transformation(self, entry: 'Entry') -> List:
        translator = DCTitleTranslator()
        phaidra_data = translator.translate_data(entry)
        self.assertEqual(
            phaidra_data,
            [
                {
                    '@type': 'bf:Title',
                    'bf:mainTitle': [{'@value': self._title, '@language': 'und'}],
                }
            ],
        )
        return phaidra_data

    def _only_subtitle_data_transformation(self, entry: 'Entry') -> List:
        translator = DCTitleTranslator()
        phaidra_data = translator.translate_data(entry)
        self.assertEqual(
            phaidra_data,
            [
                {
                    '@type': 'bf:Title',
                    'bf:mainTitle': [{'@language': 'und', '@value': ''}],  # default '', not nullable
                    'bf:subtitle': [{'@value': self._subtitle, '@language': 'und'}],
                }
            ],
        )
        return phaidra_data

    def _only_title_validation(self, data: List) -> Dict[int, Dict]:
        schema = DceTitleSchema()
        errors = {key: schema.validate(datum) for key, datum in enumerate(data)}
        self.assertEqual(
            errors,
            {
                0: {},
            },
        )
        return errors

    def _only_subtitle_validation(self, data: List) -> Dict[int, Dict]:
        self.assertEqual(
            data.__len__(), 1, 'if data is not length 1, this test does not makes sense. Data should be default 1'
        )  # !
        schema = DceTitleSchema()
        errors: Dict[int, Dict] = {key: schema.validate(datum) for key, datum in enumerate(data)}
        self.assertEqual(
            errors,
            {
                0: {},  # title defaults to empty string, though not nullable
            },
        )
        return errors

    def _only_title_error_transformation(self, errors: Dict[int, Dict]) -> Dict:
        translator = DCTitleTranslator()
        portfolio_errors = translator.translate_errors(errors)
        self.assertEqual(portfolio_errors, {})
        return portfolio_errors

    def _only_subtitle_error_transformation(self, errors: Dict) -> Dict:
        translator = DCTitleTranslator()
        portfolio_errors = translator.translate_errors(errors)
        self.assertEqual(
            portfolio_errors,
            {
                # title defaults to empty string in db
                # 'title': [MISSING_DATA_FOR_REQUIRED_FIELD],
            },
        )
        return portfolio_errors


class EdmHastypeTestCase(TestCase):
    """Nothing in phaidra checks, but in legacy templates."""

    _entry: Optional['Entry'] = None

    example_type_data = {
        'label': {'de': 'Artikel', 'en': 'article'},
        'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/article',
    }

    expected_translated_data = [
        {
            '@type': 'skos:Concept',
            'skos:prefLabel': [
                {
                    '@value': 'Artikel',
                    '@language': 'deu',
                },
                {
                    '@value': 'article',
                    '@language': 'eng',
                },
            ],
            'skos:exactMatch': [
                'http://base.uni-ak.ac.at/portfolio/taxonomy/article',
            ],
        }
    ]

    @property
    def entry(self) -> Entry:
        """To make sure _example data is correct!

        :return:
        """
        if self._entry is None:
            self._entry = Entry(
                title='Panda Shampoo Usage In Northern Iraq',
                owner=User.objects.create_user(username='Quatschenstein', email='port@folio.ac.at'),
                type=self.example_type_data,
            )
            self._entry.clean_fields()
            self._entry.save()
        return self._entry

    def test_translate_data(self):
        entry = self.entry
        translated_data = EdmHasTypeTranslator().translate_data(entry)
        self.assertEqual(translated_data, self.expected_translated_data)

    def test_validate_data(self):
        schema = SkosConceptSchema()
        validation = [schema.validate(datum) for datum in self.expected_translated_data]
        self.assertEqual(
            validation,
            [
                {},
            ],
        )

    def test_validate_faulty_data(self):
        translated_data = deepcopy(self.expected_translated_data)
        translated_datum = translated_data[0]
        del translated_datum['skos:exactMatch']
        schema = SkosConceptSchema()
        validation = schema.validate(translated_datum)
        self.assertEqual(
            validation,
            {
                'skos:exactMatch': [MISSING_DATA_FOR_REQUIRED_FIELD],
            },
        )

    def test_translate_errors(self):
        errors = {
            0: {
                'skos:exactMatch': [MISSING_DATA_FOR_REQUIRED_FIELD],
            },
        }
        self.assertEqual(
            {
                'type': [
                    MISSING_DATA_FOR_REQUIRED_FIELD,
                ]
            },
            EdmHasTypeTranslator().translate_errors(errors),
        )

    def test_incomplete_input_data_label(self):
        data = deepcopy(self.example_type_data)
        del data['label']
        entry = Entry(type=data)
        self.assertEqual(
            EdmHasTypeTranslator().translate_data(entry),
            [
                {
                    '@type': 'skos:Concept',
                    'skos:prefLabel': [],
                    'skos:exactMatch': [
                        'http://base.uni-ak.ac.at/portfolio/taxonomy/article',
                    ],
                }
            ],
        )

    def test_incomplete_input_data_source(self):
        data = deepcopy(self.example_type_data)
        del data['source']
        entry = Entry(type=data)
        self.assertEqual(
            EdmHasTypeTranslator().translate_data(entry),
            [
                {
                    '@type': 'skos:Concept',
                    'skos:prefLabel': [
                        {
                            '@value': 'Artikel',
                            '@language': 'deu',
                        },
                        {
                            '@value': 'article',
                            '@language': 'eng',
                        },
                    ],
                    'skos:exactMatch': [],
                }
            ],
        )

    def test_empty_input_data(self):
        entry = Entry()
        self.assertEqual(EdmHasTypeTranslator().translate_data(entry), [])


class GenericSkosConceptTestCase(TestCase):
    def test_get_data_missing_key_fail(self):
        entry = Entry(data={'other-stuff': ';-)'})
        translator = GenericSkosConceptTranslator('data', ['not-existing-key'], raise_on_not_found_error=True)
        self.assertRaises(KeyError, lambda: translator._get_data_of_interest(entry))

    def test_get_data_missing_key_fallback(self):
        entry = Entry(data={'other-stuff': ';-)'})
        translator = GenericSkosConceptTranslator('data', ['not-existing-key'], raise_on_not_found_error=False)
        self.assertEqual([], translator._get_data_of_interest(entry))

    def test_get_materials_data(self):
        materials_data = (
            [
                {
                    'label': {'de': 'CD-Rom', 'en': 'CD-Rom'},
                    'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/cd-rom',
                }
            ],
        )
        entry = Entry(data={'material': materials_data})
        translator = GenericSkosConceptTranslator('data', ['material'], raise_on_not_found_error=False)
        self.assertEqual(materials_data, translator._get_data_of_interest(entry))

    def test_get_keywords_data(self):
        keywords = [
            {
                'label': {'de': 'Airbrush', 'en': 'Airbrushing'},
                'source': 'http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e',
            }
        ]
        entry = Entry(keywords=keywords)
        translator = GenericSkosConceptTranslator('keywords')
        self.assertEqual(keywords, translator._get_data_of_interest(entry))

    def test_translate_keywords(self):
        translator = GenericSkosConceptTranslator('keywords')
        self.assertEqual(
            translator._translate(
                [
                    {
                        'label': {'de': 'Airbrush', 'en': 'Airbrushing'},
                        'source': 'http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e',
                    }
                ]
            ),
            [
                {
                    '@type': 'skos:Concept',
                    'skos:exactMatch': [
                        'http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e',
                    ],
                    'skos:prefLabel': [
                        {
                            '@value': 'Airbrush',
                            '@language': 'deu',
                        },
                        {
                            '@value': 'Airbrushing',
                            '@language': 'eng',
                        },
                    ],
                }
            ],
        )

    def test_full_translation(self):
        entry = Entry(
            keywords=[
                {
                    'label': {'de': 'Airbrush', 'en': 'Airbrushing'},
                    'source': 'http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e',
                }
            ]
        )
        translator = GenericSkosConceptTranslator('keywords')
        self.assertEqual(
            translator.translate_data(entry),
            [
                {
                    '@type': 'skos:Concept',
                    'skos:exactMatch': [
                        'http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e',
                    ],
                    'skos:prefLabel': [
                        {
                            '@value': 'Airbrush',
                            '@language': 'deu',
                        },
                        {
                            '@value': 'Airbrushing',
                            '@language': 'eng',
                        },
                    ],
                }
            ],
        )

    def test_validate_correct_input(self):
        schema = SkosConceptSchema()
        errors = schema.validate(
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': [
                    'http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e',
                ],
                'skos:prefLabel': [
                    {
                        '@value': 'Airbrush',
                        '@language': 'deu',
                    },
                    {
                        '@value': 'Airbrushing',
                        '@language': 'eng',
                    },
                ],
            }
        )
        self.assertEqual(errors, {})

    def test_validate_incorrect_input(self):
        schema = SkosConceptSchema()
        errors = schema.validate(
            {
                '@type': 'skos:Concept',
                'skos:prefLabel': [
                    {
                        '@value': 'Airbrush',
                        '@language': 'deu',
                    },
                    {
                        '@value': 'Airbrushing',
                        '@language': 'eng',
                    },
                ],
            }
        )
        self.assertEqual(errors, {'skos:exactMatch': [MISSING_DATA_FOR_REQUIRED_FIELD]})

    def test_error_translation_empty(self):
        self.assertEqual({}, GenericSkosConceptTranslator('not-important', []).translate_errors([]))

    def test_error_translation(self):
        self.assertRaises(
            InternalValidationError,
            lambda: GenericSkosConceptTranslator('not-important', []).translate_errors(
                [
                    {'skos:exactMatch': [MISSING_DATA_FOR_REQUIRED_FIELD]},
                ]
            ),
        )


class BfNoteTestCase(TestCase):
    def test_translate_data_correct_default_case(self):
        entry = Entry(
            texts=[
                {
                    'data': [
                        {'text': 'Any Text', 'language': {'source': 'http://base.uni-ak.ac.at/portfolio/languages/en'}}
                    ]
                },
            ]
        )
        translator = BfNoteTranslator()
        self.assertEqual(
            translator.translate_data(entry),
            [
                {
                    '@type': 'bf:Note',
                    'skos:prefLabel': [
                        {
                            '@value': 'Any Text',
                            '@language': 'eng',
                        }
                    ],
                },
            ],
        )

    def test_translate_data_correct_abstract_text_type_case(self):
        entry = Entry(
            texts=[
                {
                    'data': [
                        {
                            'text': 'Abstract Text!',
                            'language': {'source': 'http://base.uni-ak.ac.at/portfolio/languages/de'},
                        }
                    ],
                    'type': {
                        'label': {'de': 'Abstract', 'en': 'Abstract'},
                        'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract',
                    },
                }
            ]
        )
        translator = BfNoteTranslator()
        self.assertEqual(
            translator.translate_data(entry),
            [
                {
                    '@type': 'bf:Summary',
                    'skos:prefLabel': [
                        {
                            '@value': 'Abstract Text!',
                            '@language': 'deu',
                        }
                    ],
                },
            ],
        )

    def test_translate_faulty_data(self):
        self.assertRaises(TypeError, lambda: BfNoteTranslator().translate_data(Entry(texts=23)))

    def test_validate_data_correct(self):
        schema = TypeLabelSchema()
        self.assertEqual(
            {},
            schema.validate(
                {
                    '@type': 'bf:Summary',
                    'skos:prefLabel': [
                        {
                            '@value': 'Abstract Text!',
                            '@language': 'deu',
                        }
                    ],
                },
            ),
        )

    def test_validate_data_error(self):
        schema = TypeLabelSchema()
        self.assertEqual(
            {
                '@type': [MISSING_DATA_FOR_REQUIRED_FIELD],
            },
            schema.validate(
                {
                    'skos:prefLabel': [
                        {
                            '@value': 'Abstract Text!',
                            '@language': 'deu',
                        }
                    ]
                },
            ),
        )

    def test_translate_errors_empty(self):
        self.assertEqual({}, BfNoteTranslator().translate_errors({}))

    def test_translate_error_not_empty(self):
        self.assertRaises(
            InternalValidationError,
            lambda: BfNoteTranslator().translate_errors(
                [
                    {
                        '@type': [MISSING_DATA_FOR_REQUIRED_FIELD],
                    }
                ]
            ),
        )


class StaticGenericPersonTestCase(TestCase):
    def test_translate_empty_data(self):
        translator = GenericStaticPersonTranslator(
            primary_level_data_key='editors', role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/editor'
        )
        entry = Entry(data={})
        self.assertEqual([], translator.translate_data(entry))

    def test_translate_data_correct(self):
        entry = Entry(
            data={
                'authors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Autor*in', 'en': 'Author'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/author',
                            }
                        ],
                        'source': 'http://d-nb.info/gnd/5299671-2',
                    }
                ]
            }
        )
        translator = GenericStaticPersonTranslator(
            primary_level_data_key='authors', role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author'
        )
        self.assertEqual(
            translator.translate_data(entry),
            [
                {
                    '@type': 'schema:Person',
                    'skos:exactMatch': [
                        {
                            '@value': 'http://d-nb.info/gnd/5299671-2',
                            '@type': 'ids:uri',
                        },
                    ],
                    'schema:name': [
                        {
                            '@value': 'Universität für Angewandte Kunst Wien',
                        }
                    ],
                },
            ],
        )

    def test_translate_faulty_data(self):
        entry = Entry(
            data={
                'authors': [
                    {
                        'label-got-wrong': 'Universität für Angewandte Kunst Wien',
                        'source': 'http://d-nb.info/gnd/5299671-2',
                    }
                ]
            }
        )
        translator = GenericStaticPersonTranslator(
            primary_level_data_key='authors', role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author'
        )
        self.assertRaises(KeyError, lambda: translator.translate_data(entry))

    def test_validate_data_correct(self):
        person_schema = PersonSchema()
        self.assertEqual(
            {},
            person_schema.validate(
                {
                    '@type': 'schema:Person',
                    'skos:exactMatch': [
                        {
                            '@value': 'http://d-nb.info/gnd/5299671-2',
                            '@type': 'ids:uri',
                        },
                    ],
                    'schema:name': [
                        {
                            '@value': 'Universität für Angewandte Kunst Wien',
                        }
                    ],
                }
            ),
        )

    def test_validate_data_error(self):
        person_schema = PersonSchema()
        self.assertEqual(
            {
                'schema:name': {
                    0: {
                        '@value': [MISSING_DATA_FOR_REQUIRED_FIELD],
                    }
                }
            },
            person_schema.validate(
                {
                    '@type': 'schema:Person',
                    'skos:exactMatch': [
                        {
                            '@value': 'http://d-nb.info/gnd/5299671-2',
                            '@type': 'ids:uri',
                        },
                    ],
                }
            ),
        )

    def test_translate_errors_empty(self):
        errors = {}
        translator = GenericStaticPersonTranslator(
            primary_level_data_key='authors', role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author'
        )
        self.assertEqual({}, translator.translate_errors(errors))

    def test_translate_error_not_empty(self):
        errors = [
            {
                'schema:name': {
                    0: {
                        '@value': [MISSING_DATA_FOR_REQUIRED_FIELD],
                    }
                }
            },
        ]
        translator = GenericStaticPersonTranslator(
            primary_level_data_key='authors', role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author'
        )
        self.assertRaises(InternalValidationError, lambda: translator.translate_errors(errors))


class RecursiveErrorFilterTestCase(TestCase):
    translator = PhaidraMetaDataTranslator()

    def test_normal_errors(self):
        some_errors = {
            'level-1-A': ['error-1', 'error-2'],
            'level-1-B': {
                'level-2-A': [
                    'error-3',
                ]
            },
        }
        filtered_errors = self.translator._filter_errors(some_errors)
        self.assertEqual(some_errors, filtered_errors)

    def test_nested_empty_errors_dict(self):
        some_errors = {
            'level-1-A': ['error-1', 'error-2'],
            'level-1-B': {
                # None, but there, since generating object was not aware of upper level
            },
        }
        filtered_errors = self.translator._filter_errors(some_errors)
        self.assertEqual(
            filtered_errors,
            {
                'level-1-A': ['error-1', 'error-2'],
            },
        )

    def test_nested_empty_errors_list(self):
        some_errors = {
            'level-1-A': ['error-1', 'error-2'],
            'level-1-B': [  # this time a list of empty error objects!
                {
                    # None, but there, since generating object was not aware of upper level
                }
            ],
        }
        filtered_errors = self.translator._filter_errors(some_errors)
        self.assertEqual(
            filtered_errors,
            {
                'level-1-A': ['error-1', 'error-2'],
            },
        )


class DynamicPersonsTestCase(TestCase):
    def test_translate_empty_data(self):
        entry = Entry()
        translator = PhaidraMetaDataTranslator()
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_data = translator._get_data_with_dynamic_structure(entry, mapping)
        self.assertEqual(
            {},
            dynamic_data,
        )

    def test_translate_data_correct(self):
        entry = Entry(
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            }
        )

        translator = PhaidraMetaDataTranslator()
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_data = translator._get_data_with_dynamic_structure(entry, mapping)
        self.assertEqual(
            dynamic_data,
            {
                'role:act': [
                    {
                        '@type': 'schema:Person',
                        'skos:exactMatch': [],
                        'schema:name': [
                            {
                                '@value': 'Universität für Angewandte Kunst Wien',
                            },
                        ],
                    },
                ],
            },
        )

    def test_translate_faulty_data(self):
        entry = Entry(
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        # 'roles': [],
                    },
                ],
            }
        )

        translator = PhaidraMetaDataTranslator()
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        self.assertEqual(
            translator._get_data_with_dynamic_structure(entry, mapping),
            {},
        )

    def test_validate_data_correct(self):
        entry = Entry(
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            }
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        Schema = get_phaidra_meta_data_schema_with_dynamic_fields(mapping)
        self.assertIsInstance(Schema, _PhaidraMetaData)
        self.assertIn('role_act', Schema.fields)
        self.assertEqual('role:act', Schema.fields['role_act'].load_from)
        self.assertIs(Schema.fields['role_act'].nested, PersonSchema)
        generated_schema = Schema.fields['role_act'].nested()
        self.assertEqual(
            {},
            generated_schema.validate(
                {
                    '@type': 'schema:Person',
                    'skos:exactMatch': [],
                    'schema:name': [
                        {
                            '@value': 'Universität für Angewandte Kunst Wien',
                        },
                    ],
                },
            ),
        )

    def test_validate_data_error(self):
        entry = Entry(
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            }
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        Schema = get_phaidra_meta_data_schema_with_dynamic_fields(mapping)
        generated_schema = Schema.fields['role_act'].nested()
        self.assertEqual(
            {
                'skos:exactMatch': {
                    0: {
                        '@value': [MISSING_DATA_FOR_REQUIRED_FIELD],
                    },
                },
            },
            generated_schema.validate(
                {
                    '@type': 'schema:Person',
                    # 'skos:exactMatch': [],
                    'schema:name': [
                        {
                            '@value': 'Universität für Angewandte Kunst Wien',
                        },
                    ],
                },
            ),
        )

    def test_translate_errors_empty(self):
        translator = PhaidraMetaDataTranslator()
        entry = Entry(
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            }
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        self.assertEqual({}, translator._translate_errors_with_dynamic_structure({}, mapping))

    def test_translate_error_not_empty(self):
        entry = Entry(
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            }
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        self.assertRaises(
            InternalValidationError,
            lambda: translator._translate_errors_with_dynamic_structure(
                contributor_role_mapping=mapping,
                errors={
                    'role:act': {
                        'skos:exactMatch': {
                            0: {
                                '@value': [MISSING_DATA_FOR_REQUIRED_FIELD],
                            },
                        },
                    }
                },
            ),
        )


class UpmostLevelStaticDataTestCase(TestCase):
    def test_translate_empty_data(self):
        entry = Entry()
        translator = PhaidraMetaDataTranslator()
        # does not raise anything :-( title is '' default, but not nullable …
        # self.assertRaises(TypeError, lambda: translator.translate_data(entry))
        self.assertEqual(
            translator.translate_data(entry),
            {
                'dcterms:type': [
                    {
                        '@type': 'skos:Concept',
                        'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                        'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
                    }
                ],
                'edm:hasType': [],
                'dce:title': [{'@type': 'bf:Title', 'bf:mainTitle': [{'@value': '', '@language': 'und'}]}],
                'dcterms:language': [],
                'dcterms:subject': [],
                'rdau:P60048': [],
                'dce:format': [],
                'bf:note': [],
                'role:edt': [],
                'role:aut': [],
                'role:pbl': [],
            },
        )

    def test_translate_minimal_correct_data(self):
        """
        This is the minimum required data from Entry - remember translation is not validation.
        Validation will take care of phaidra.
        :return:
        """
        entry = Entry(title='A Book With A Cover And No Pages At All.')
        translator = PhaidraMetaDataTranslator()
        self.assertEqual(
            translator.translate_data(entry),
            {
                'dcterms:type': [
                    {
                        '@type': 'skos:Concept',
                        'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                        'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
                    }
                ],
                'edm:hasType': [],
                'dce:title': [
                    {
                        '@type': 'bf:Title',
                        'bf:mainTitle': [{'@value': 'A Book With A Cover And No Pages At All.', '@language': 'und'}],
                    }
                ],
                'dcterms:language': [],
                'dcterms:subject': [],
                'rdau:P60048': [],
                'dce:format': [],
                'bf:note': [],
                'role:edt': [],
                'role:aut': [],
                'role:pbl': [],
            },
        )

    def test_translate_some_correct_data(self):
        entry = Entry(
            title='A Book With A Cover And No Pages At All.',
            data={
                'label': {'de': 'Installation', 'en': 'Installation'},
                'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/installation',
            },
        )
        translator = PhaidraMetaDataTranslator()
        self.assertEqual(
            translator.translate_data(entry),
            {
                'dcterms:type': [
                    {
                        '@type': 'skos:Concept',
                        'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                        'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
                    }
                ],
                'edm:hasType': [],
                'dce:title': [
                    {
                        '@type': 'bf:Title',
                        'bf:mainTitle': [{'@value': 'A Book With A Cover And No Pages At All.', '@language': 'und'}],
                    }
                ],
                'dcterms:language': [],
                'dcterms:subject': [],
                'rdau:P60048': [],
                'dce:format': [],
                'bf:note': [],
                'role:edt': [],
                'role:aut': [],
                'role:pbl': [],
            },
        )

    def test_translate_faulty_data(self):
        entry = Entry()
        translator = PhaidraMetaDataTranslator()
        # does not raise anything :-( title is '' default, but not nullable …
        # self.assertRaises(TypeError, lambda: translator.translate_data(entry))
        self.assertEqual(
            translator.translate_data(entry),
            {
                'dcterms:type': [
                    {
                        '@type': 'skos:Concept',
                        'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                        'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
                    }
                ],
                'edm:hasType': [],
                'dce:title': [{'@type': 'bf:Title', 'bf:mainTitle': [{'@value': '', '@language': 'und'}]}],
                'dcterms:language': [],
                'dcterms:subject': [],
                'rdau:P60048': [],
                'dce:format': [],
                'bf:note': [],
                'role:edt': [],
                'role:aut': [],
                'role:pbl': [],
            },
        )

    def test_validate_data_correct(self):
        minimal_correct_data = {
            'dce:title': [
                {
                    '@type': 'bf:Title',
                    'bf:mainTitle': [
                        {
                            '@value': 'A Book With A Cover And No Pages At All.',
                            '@language': 'und',
                        }
                    ],
                }
            ],
            'edm:hasType': [
                {
                    '@type': 'skos:Concept',
                    'skos:prefLabel': [
                        {
                            '@value': 'Artikel',
                            '@language': 'deu',
                        },
                        {
                            '@value': 'article',
                            '@language': 'eng',
                        },
                    ],
                    'skos:exactMatch': [
                        'http://base.uni-ak.ac.at/portfolio/taxonomy/article',
                    ],
                }
            ],
        }
        self.assertEqual({}, _PhaidraMetaData().validate(minimal_correct_data))

    def test_validate_data_error(self):
        self.assertEqual(
            _PhaidraMetaData().validate({}),
            {
                'dce:title': {
                    0: {
                        'bf:mainTitle': {
                            0: {
                                '@language': [MISSING_DATA_FOR_REQUIRED_FIELD],
                                '@value': [MISSING_DATA_FOR_REQUIRED_FIELD],
                            }
                        }
                    }
                },
            },
        )

    def test_translate_errors_empty(self):
        entry = Entry()  # whatever
        mapper = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        self.assertEqual({}, translator.translate_errors({}, mapper))


class UpmostLevelAllDataTestCase(TestCase):
    def test_translate_data_correct(self):
        entry = Entry(
            title='A Book With A Contributor',
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            },
        )
        translator = PhaidraMetaDataTranslator()
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        phaidra_data = translator.translate_data(model=entry, contributor_role_mapping=mapping)
        self.assertEqual(
            phaidra_data,
            {
                'dcterms:type': [
                    {
                        '@type': 'skos:Concept',
                        'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                        'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
                    }
                ],
                'edm:hasType': [],
                'dce:title': [
                    {
                        '@type': 'bf:Title',
                        'bf:mainTitle': [{'@value': 'A Book With A Contributor', '@language': 'und'}],
                    }
                ],
                'dcterms:language': [],
                'dcterms:subject': [],
                'rdau:P60048': [],
                'dce:format': [],
                'bf:note': [],
                'role:edt': [],
                'role:aut': [],
                'role:pbl': [],
                'role:act': [
                    {
                        '@type': 'schema:Person',
                        'skos:exactMatch': [],
                        'schema:name': [
                            {
                                '@value': 'Universität für Angewandte Kunst Wien',
                            },
                        ],
                    },
                ],
            },
        )

    def test_validate_data_correct(self):
        entry = Entry(
            title='A Book With A Contributor',
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            },
            type={
                'label': {'de': 'Artikel', 'en': 'article'},
                'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/article',
            },
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        schema = get_phaidra_meta_data_schema_with_dynamic_fields(mapping)
        transformer = PhaidraMetaDataTranslator()
        data = transformer.translate_data(entry, mapping)
        errors = schema.validate(data)
        self.assertEqual(errors, {})

    def test_validate_data_error(self):
        entry = Entry(
            title='A Book With A Contributor',
            data={
                'contributors': [
                    {
                        # 'label': 'Universität für Angewandte Kunst Wien',
                        'roles': [
                            {
                                'label': {'de': 'Darsteller*in', 'en': 'Actor'},
                                'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/actor',
                            }
                        ],
                    },
                ],
            },
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        schema = get_phaidra_meta_data_schema_with_dynamic_fields(mapping)
        self.assertEqual(
            {
                'role:act': {
                    0: {
                        'schema:name': [
                            MISSING_DATA_FOR_REQUIRED_FIELD,
                        ]
                    }
                }
            },
            schema.validate(
                {
                    'dcterms:type': [
                        {
                            '@type': 'skos:Concept',
                            'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                            'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
                        }
                    ],
                    'edm:hasType': [],
                    'dce:title': [
                        {
                            '@type': 'bf:Title',
                            'bf:mainTitle': [{'@value': 'A Book With A Contributor', '@language': 'und'}],
                        }
                    ],
                    'dcterms:subject': [],
                    'rdau:P60048': [],
                    'dce:format': [],
                    'bf:note': [],
                    'role:edt': [],
                    'role:aut': [],
                    'role:pbl': [],
                    'role:act': [
                        {
                            '@type': 'schema:Person',
                            'skos:exactMatch': [],
                            'schema:name': [
                                # nothing
                            ],
                        },
                    ],
                },
            ),
        )


class PhaidraRuleTest(TestCase):
    """Full validation stories according to https://basedev.uni-
    ak.ac.at/redmine/issues/1419 The entry must have a title.

    The entry must have a type.
    """

    def test_missing_title(self):
        entry = Entry(
            # enforce no title
            title=None,
        )
        errors = self._validate(entry)
        self.assertEqual(errors, {'title': ['Field may not be null.']})

    def test_missing_nothing(self):
        entry = Entry(
            title='Everything included!',
            type={
                'label': {'de': 'Installation', 'en': 'Installation'},
                'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/installation',
            },
        )
        errors = self._validate(entry)
        self.assertEqual(errors, {})

    def _validate(self, entry: 'Entry') -> Dict:
        """Validate phaidra style, return errors portfolio style.

        :param entry:
        :return: errors
        """
        translator = PhaidraMetaDataTranslator()
        dynamic_mapping = BidirectionalConceptsMapper.from_entry(entry)
        schema = get_phaidra_meta_data_schema_with_dynamic_fields(dynamic_mapping)

        phaidra_data = translator.translate_data(entry)
        phaidra_errors = schema.validate(phaidra_data)
        portfolio_errors = translator.translate_errors(phaidra_errors, dynamic_mapping)

        return portfolio_errors


class TranslateNotImplementedLanguageTextTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_translate_only_not_implemented(self):
        entry = self.model_provider.get_entry(german_abstract=False, english_abstract=False, french_abstract=True)
        dynamic_mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        translation = translator.translate_data(entry, dynamic_mapping)
        bf_note: List[Dict] = translation['bf:note']
        self.assertEqual(0, len(bf_note))

    def test_mixed(self):
        entry = self.model_provider.get_entry(german_abstract=True, english_abstract=True, french_abstract=True)
        dynamic_mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        translation = translator.translate_data(entry, dynamic_mapping)
        bf_note: List[Dict] = translation['bf:note']
        self.assertEqual(2, len(bf_note))

    def test_implemented(self):
        entry = self.model_provider.get_entry(german_abstract=True, english_abstract=True, french_abstract=False)
        dynamic_mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        translation = translator.translate_data(entry, dynamic_mapping)
        bf_note: List[Dict] = translation['bf:note']
        self.assertEqual(2, len(bf_note))


class TranslateLanguageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_akan(self):
        entry = self.model_provider.get_entry(akan_language=True, german_language=False)
        dynamic_mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        translation = translator.translate_data(entry, dynamic_mapping)
        self.assertEqual(
            1,
            translation['dcterms:language'].__len__(),
        )

    def test_german(self):
        entry = self.model_provider.get_entry(german_language=True, akan_language=False)
        dynamic_mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        translation = translator.translate_data(entry, dynamic_mapping)
        self.assertEqual(
            1,
            translation['dcterms:language'].__len__(),
        )

    def test_akan_and_german(self):
        entry = self.model_provider.get_entry(german_language=True, akan_language=True)
        dynamic_mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraMetaDataTranslator()
        translation = translator.translate_data(entry, dynamic_mapping)
        self.assertEqual(
            2,
            translation['dcterms:language'].__len__(),
        )


class ThesisSwitchArchiverTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_with_entry_no_type(self):
        """Should return no default type."""
        entry = self.model_provider.get_entry(type_=False)
        media = self.model_provider.get_media(entry)
        controller = DefaultArchiveController(user=self.model_provider.user, media_primary_keys={media.id})
        archiver: 'PhaidraArchiver' = controller.archiver
        metadata_data_archiver: 'DefaultMetadataArchiver' = archiver.metadata_data_archiver
        self.assertIsInstance(metadata_data_archiver, DefaultMetadataArchiver)
        self.assertEqual(metadata_data_archiver.base_schema_class, _PhaidraMetaData)
        self.assertEqual(metadata_data_archiver.translator_class, PhaidraMetaDataTranslator)

    def test_entry_not_thesis_type(self):
        """Should return no default type."""
        entry = self.model_provider.get_entry(type_=True, thesis_type=False)
        media = self.model_provider.get_media(entry)
        controller = DefaultArchiveController(user=self.model_provider.user, media_primary_keys={media.id})
        archiver: 'PhaidraArchiver' = controller.archiver
        metadata_data_archiver: 'DefaultMetadataArchiver' = archiver.metadata_data_archiver
        self.assertIsInstance(metadata_data_archiver, DefaultMetadataArchiver)
        self.assertEqual(metadata_data_archiver.base_schema_class, _PhaidraMetaData)
        self.assertEqual(metadata_data_archiver.translator_class, PhaidraMetaDataTranslator)

    def test_entry_thesis_type(self):
        """Should return no thesis type."""
        entry = self.model_provider.get_entry(type_=True, thesis_type=True)
        media = self.model_provider.get_media(entry)
        controller = DefaultArchiveController(user=self.model_provider.user, media_primary_keys={media.id})
        archiver: 'PhaidraArchiver' = controller.archiver
        metadata_data_archiver: 'ThesisMetadataArchiver' = archiver.metadata_data_archiver
        self.assertIsInstance(metadata_data_archiver, ThesisMetadataArchiver)
        self.assertEqual(metadata_data_archiver.base_schema_class, _PhaidraThesisMetaDataSchema)
        self.assertEqual(metadata_data_archiver.translator_class, PhaidraThesisMetaDataTranslator)


class ThesisSwitchSchemaTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def _get_schema(self, type_=True, thesis_type=True):
        """Mimicks media_server.archiver.implementations.phaidra.metadata.archi
        ver.DefaultMetadataArchiver.validate."""
        entry = self.model_provider.get_entry(type_, thesis_type)
        media = self.model_provider.get_media(entry)
        controller = DefaultArchiveController(user=self.model_provider.user, media_primary_keys={media.id})
        archiver: 'PhaidraArchiver' = controller.archiver
        metadata_data_archiver: 'DefaultMetadataArchiver' = archiver.metadata_data_archiver
        contributor_role_mapping = metadata_data_archiver.mapper_class.from_entry(
            metadata_data_archiver.archive_object.entry
        )
        return get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=contributor_role_mapping,
            base_schema_class=metadata_data_archiver.base_schema_class,
        )

    def test_with_entry_no_type(self):
        schema = self._get_schema(type_=False)
        self.assertIsInstance(schema, _PhaidraMetaData)

    def test_entry_not_thesis_type(self):
        schema = self._get_schema(type_=True, thesis_type=False)
        self.assertIsInstance(schema, _PhaidraMetaData)

    def test_entry_thesis_type(self):
        schema = self._get_schema(type_=True, thesis_type=True)
        self.assertIsInstance(schema, _PhaidraThesisMetaDataSchema)


class TitleExistsTestCase(TestCase):
    """According to frontend devs, title is not found in not thesis
    metadata."""

    expected_title = [
        {
            '@type': 'bf:Title',
            'bf:mainTitle': [
                {'@value': 'A Title', '@language': 'und'},
            ],
        },
    ]

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_title_generation_from_thesis(self):
        entry = self.model_provider.get_entry()
        media = self.model_provider.get_media(entry=entry)
        archiver = DefaultMetadataArchiver(
            ArchiveObject(user=self.model_provider.user, entry=entry, media_objects={media})
        )
        archiver.validate()
        self.assertIn('dce:title', archiver.data)
        self.assertEqual(1, archiver.data['dce:title'].__len__())
        self.assertEqual(archiver.data['dce:title'], self.expected_title)

    def test_title_generation_from_not_thesis(self):
        entry = self.model_provider.get_entry(thesis_type=False)
        media = self.model_provider.get_media(entry=entry)
        archiver = DefaultMetadataArchiver(
            ArchiveObject(user=self.model_provider.user, entry=entry, media_objects={media})
        )
        archiver.validate()
        self.assertIn('dce:title', archiver.data)
        self.assertEqual(1, archiver.data['dce:title'].__len__())
        self.assertEqual(archiver.data['dce:title'], self.expected_title)
