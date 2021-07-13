"""https://basedev.uni-ak.ac.at/redmine/issues/1419."""
from copy import deepcopy
from typing import Dict, List, Optional

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.datatranslation import (
    BfNoteTranslator,
    DCTitleTranslator,
    EdmHasTypeTranslator,
    GenericSkosConceptTranslator,
    GenericStaticPersonTranslator,
    PhaidraMetaDataTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    BidirectionalConceptsMapper,
)
from media_server.archiver.implementations.phaidra.metadata.schemas import (
    DceTitleSchema,
    PersonSchema,
    SkosConceptSchema,
    TypeLabelSchema,
    _PhaidraMetaData,
    get_phaidra_meta_data_schema_with_dynamic_fields,
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
            [
                {},
            ],
        )
        portfolio_errors = self._only_title_error_transformation(phaidra_errors)
        self.assertEqual(portfolio_errors, {})

    def test_only_subtitle_data_flow(self):
        entry = Entry(subtitle=self._subtitle)
        phaidra_data = self._only_subtitle_data_transformation(entry)
        self.assertIs(phaidra_data.__class__, list)  # detailed test in _method
        phaidra_errors = self._only_subtitle_validation(phaidra_data)
        self.assertEqual(len(phaidra_errors), 1)
        self.assertIs(phaidra_errors.__class__, list)
        portfolio_errors = self._only_subtitle_error_transformation(phaidra_errors)
        self.assertEqual(len(portfolio_errors), 1)  # details in _method

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
                    'bf:subtitle': [{'@value': self._subtitle, '@language': 'und'}],
                }
            ],
        )
        return phaidra_data

    def _only_title_validation(self, data: List) -> List:
        schema = DceTitleSchema()
        errors = [schema.validate(datum) for datum in data]
        self.assertEqual(
            errors,
            [
                {},
            ],
        )
        return errors

    def _only_subtitle_validation(self, data: List) -> List[Dict]:
        self.assertEqual(
            data.__len__(), 1, 'if data is not length 1, this test does not makes sense. Data should be default 1'
        )  # !
        schema = DceTitleSchema()
        errors: List = [schema.validate(datum) for datum in data]
        self.assertEqual(
            errors,
            [
                {
                    'bf:mainTitle': {
                        0: {
                            '@value': [
                                'Missing data for required field.',
                            ],
                            '@language': [
                                'Missing data for required field.',
                            ],
                        }
                    }
                }
            ],
        )
        return errors

    def _only_title_error_transformation(self, errors: List[Dict]) -> Dict:
        translator = DCTitleTranslator()
        portfolio_errors = translator.translate_errors(errors)
        self.assertEqual(portfolio_errors, {})
        return portfolio_errors

    def _only_subtitle_error_transformation(self, errors: List) -> Dict:
        translator = DCTitleTranslator()
        portfolio_errors = translator.translate_errors(errors)
        self.assertEqual(
            portfolio_errors,
            {
                'title': ['Missing data for required field.'],
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
                'skos:exactMatch': ['Missing data for required field.'],
            },
        )

    def test_translate_errors(self):
        errors = [
            {
                'skos:exactMatch': ['Missing data for required field.'],
            },
        ]
        self.assertRaises(
            InternalValidationError,
            lambda: EdmHasTypeTranslator().translate_errors(errors),
        )

    def test_faulty_input_data_label(self):
        data = deepcopy(self.example_type_data)
        del data['label']
        entry = Entry(type=data)
        self.assertRaises(RuntimeError, lambda: EdmHasTypeTranslator().translate_data(entry))

    def test_faulty_input_data_source(self):
        data = deepcopy(self.example_type_data)
        del data['source']
        entry = Entry(type=data)
        self.assertRaises(RuntimeError, lambda: EdmHasTypeTranslator().translate_data(entry))

    def test_empty_input_data(self):
        entry = Entry()
        self.assertRaises(RuntimeError, lambda: EdmHasTypeTranslator().translate_data(entry))


class GenericSkosConceptTestCase(TestCase):
    def test_get_data_missing_key_fail(self):
        entry = Entry(data={'other-stuff': ';-)'})
        translator = GenericSkosConceptTranslator('data', ['not-existing-key'], raise_on_key_error=True)
        self.assertRaises(KeyError, lambda: translator._get_data_of_interest(entry))

    def test_get_data_missing_key_fallback(self):
        entry = Entry(data={'other-stuff': ';-)'})
        translator = GenericSkosConceptTranslator('data', ['not-existing-key'], raise_on_key_error=False)
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
        translator = GenericSkosConceptTranslator('data', ['material'], raise_on_key_error=False)
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
        self.assertEqual(errors, {'skos:exactMatch': ['Missing data for required field.']})

    def test_error_translation_empty(self):
        self.assertEqual([], GenericSkosConceptTranslator('not-important', []).translate_errors([]))

    def test_error_translation(self):
        self.assertRaises(
            InternalValidationError,
            lambda: GenericSkosConceptTranslator('not-important', []).translate_errors(
                [
                    {'skos:exactMatch': ['Missing data for required field.']},
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
                '@type': ['Missing data for required field.'],
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
        self.assertEqual([{}], BfNoteTranslator().translate_errors([{}]))

    def test_translate_error_not_empty(self):
        self.assertRaises(
            InternalValidationError,
            lambda: BfNoteTranslator().translate_errors(
                [
                    {
                        '@type': ['Missing data for required field.'],
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
                        '@value': ['Missing data for required field.'],
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
        errors = [
            {},
        ]
        translator = GenericStaticPersonTranslator(
            primary_level_data_key='authors', role_uri='http://base.uni-ak.ac.at/portfolio/vocabulary/author'
        )
        self.assertEqual([{}], translator.translate_errors(errors))

    def test_translate_error_not_empty(self):
        errors = [
            {
                'schema:name': {
                    0: {
                        '@value': ['Missing data for required field.'],
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
        self.assertRaises(KeyError, lambda: translator._get_data_with_dynamic_structure(entry, mapping))

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
        raise NotImplementedError()

    def test_translate_errors_empty(self):
        raise NotImplementedError()

    def test_translate_error_not_empty(self):
        raise NotImplementedError()
