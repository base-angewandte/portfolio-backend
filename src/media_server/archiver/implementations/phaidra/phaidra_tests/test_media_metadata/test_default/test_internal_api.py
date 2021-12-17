import importlib
from copy import deepcopy
from typing import TYPE_CHECKING, Dict, List, Optional

from media_server.archiver.implementations.phaidra.metadata.archiver import (
    DefaultMetadataArchiver,
    ThesisMetadataArchiver,
)
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import (
    PhaidraThesisMetaDataTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import (
    PhaidraThesisContainer,
    PhaidraThesisMetaData,
    create_dynamic_phaidra_thesis_meta_data_schema,
)
from media_server.archiver.interface.archiveobject import ArchiveObject
from media_server.archiver.messages.validation import MISSING_DATA_FOR_REQUIRED_FIELD
from media_server.archiver.messages.validation.thesis import MISSING_AUTHOR

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
    PhaidraContainer,
    PhaidraMetaData,
    SkosConceptSchema,
    TypeLabelSchema,
)
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    BidirectionalConceptsMapper,
)
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider, \
    FakeBidirectionalConceptsMapper
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


class MissingTypeTestCase(TestCase):
    """Type is not mandatory."""

    _entry: Optional['Entry'] = None

    expected_translated_data = {
        'metadata': {
            'json-ld': {
                'dcterms:type': [
                    {
                        '@type': 'skos:Concept',
                        '' 'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                        'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
                    }
                ],
                'edm:hasType': [],
                'dce:title': [
                    {
                        '@type': 'bf:Title',
                        'bf:mainTitle': [{'@value': 'Panda Shampoo Usage In Northern Iraq', '@language': 'und'}],
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
                'bf:physicalLocation': [],
                'rdfs:seeAlso': [],
            }
        }
    }

    @property
    def entry(self) -> Entry:
        """To make sure _example data is correct!

        :return:
        """
        if self._entry is None:
            self._entry = Entry(
                title='Panda Shampoo Usage In Northern Iraq',
                owner=User.objects.create_user(username='Quatschenstein', email='port@folio.ac.at'),
            )
            self._entry.save()
        return self._entry

    def test_translate_data(self):
        entry = self.entry
        # noinspection PyTypeChecker
        translated_data = PhaidraMetaDataTranslator(
            FakeBidirectionalConceptsMapper.from_entry(entry)
        ).translate_data(entry)
        self.assertEqual(translated_data, self.expected_translated_data)

    def test_validate_data(self):
        schema = PhaidraMetaData()
        validation = schema.validate(self.expected_translated_data)
        self.assertEqual(validation, {})


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
    # noinspection PyTypeChecker
    translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_base_uris(set()))

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
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraThesisMetaDataTranslator(mapping)
        dynamic_data = translator._get_data_with_dynamic_structure(entry)
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

        mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraThesisMetaDataTranslator(mapping)
        dynamic_data = translator._get_data_with_dynamic_structure(entry)
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

    def test_translate_no_role_contributors(self):
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

        mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraThesisMetaDataTranslator(mapping)
        data = translator._get_data_with_dynamic_structure(entry)
        self.assertIn(
            'role:ctb',
            data,
        )
        ctbs = data['role:ctb']
        self.assertEqual(len(ctbs), 1)
        ctb = ctbs[0]
        self.assertEqual(ctb['schema:name'][0]['@value'], 'Universität für Angewandte Kunst Wien')

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
        schema = create_dynamic_phaidra_thesis_meta_data_schema(mapping)
        # get rid of outer layers
        schema = schema.fields['metadata'].nested.fields['json_ld'].nested
        self.assertIsInstance(schema, PhaidraContainer)
        self.assertIn('role_act', schema.fields)
        self.assertEqual('role:act', schema.fields['role_act'].load_from)
        self.assertEqual(schema.fields['role_act'].nested, PersonSchema)
        generated_schema = schema.fields['role_act'].nested()
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
        schema = create_dynamic_phaidra_thesis_meta_data_schema(mapping)
        generated_schema = schema.fields['metadata'].nested.fields['json_ld'].nested.fields['role_act'].nested()
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
        translator = PhaidraThesisMetaDataTranslator(mapping)
        self.assertEqual({}, translator._translate_errors_with_dynamic_structure({}))

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
        translator = PhaidraThesisMetaDataTranslator(mapping)
        portfolio_errors = translator._translate_errors_with_dynamic_structure(
                errors={
                    'role:act': [MISSING_DATA_FOR_REQUIRED_FIELD],
                },
            )
        expected_errors = {'data': {'contributors': [MISSING_DATA_FOR_REQUIRED_FIELD, ]}}
        self.assertEqual(expected_errors, portfolio_errors)


class StaticDataTestCase(TestCase):
    def test_translate_empty_data(self):
        entry = Entry()
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        # does not raise anything :-( title is '' default, but not nullable …
        # self.assertRaises(TypeError, lambda: translator.translate_data(entry))
        data = translator.translate_data(entry)
        # we do not want to deal with the outer scope
        data = translator._extract_from_container(data)
        self.assertEqual(
            data,
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
                'bf:physicalLocation': [],
                'rdfs:seeAlso': [],
            },
        )

    def test_translate_minimal_correct_data(self):
        """
        This is the minimum required data from Entry - remember translation is not validation.
        Validation will take care of phaidra.
        :return:
        """
        entry = Entry(title='A Book With A Cover And No Pages At All.')
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        data = translator.translate_data(entry)
        data = translator._extract_from_container(data)
        self.assertEqual(
            data,
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
                'bf:physicalLocation': [],
                'rdfs:seeAlso': [],
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
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        data = translator.translate_data(entry)
        # we do not want to deal with the outer scope
        data = translator._extract_from_container(data)
        self.assertEqual(
            data,
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
                'bf:physicalLocation': [],
                'rdfs:seeAlso': [],
            },
        )

    def test_translate_faulty_data(self):
        entry = Entry()
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        # does not raise anything :-( title is '' default, but not nullable …
        # self.assertRaises(TypeError, lambda: translator.translate_data(entry))
        data = translator.translate_data(entry)
        # I am to lazy, to write all levels, that do no count here
        data = translator._extract_from_container(data)
        self.assertEqual(
            data,
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
                'bf:physicalLocation': [],
                'rdfs:seeAlso': [],
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
        self.assertEqual({}, PhaidraContainer().validate(minimal_correct_data))

    def test_validate_data_error(self):
        self.assertEqual(
            PhaidraContainer().validate({}),
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
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_base_uris(set()))
        self.assertEqual({}, translator.translate_errors({}))


class PhaidraRuleTest(TestCase):
    """Full validation stories according to https://basedev.uni-
    ak.ac.at/redmine/issues/1419 The entry must have a title.

    The entry must have a type.
    """

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_missing_title(self):
        entry = self.model_provider.get_entry(title=False)
        errors = self._validate(entry)
        # title defaults to '' = empty string
        self.assertEqual(errors, {})

    def test_missing_nothing(self):
        entry = self.model_provider.get_entry(title=True)
        errors = self._validate(entry)
        self.assertEqual(errors, {})

    def _validate(self, entry: 'Entry') -> Dict:
        """Validate phaidra style, return errors portfolio style.

        :param entry:
        :return: errors
        """
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        schema = PhaidraMetaData()
        phaidra_data = translator.translate_data(entry)
        phaidra_errors = schema.validate(phaidra_data)
        portfolio_errors = translator.translate_errors(phaidra_errors)
        return portfolio_errors


class TranslateNotImplementedLanguageTextTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_translate_only_not_implemented(self):
        entry = self.model_provider.get_entry(german_abstract=False, english_abstract=False, french_abstract=True)
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        translation = translator.translate_data(entry)
        # only check dynamic part
        translation = translator._extract_from_container(translation)
        bf_note: List[Dict] = translation['bf:note']
        self.assertEqual(1, len(bf_note))

    def test_mixed(self):
        entry = self.model_provider.get_entry(german_abstract=True, english_abstract=True, french_abstract=True)
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        translation = translator.translate_data(entry)
        # only check dynamic part
        translation = translator._extract_from_container(translation)
        bf_note: List[Dict] = translation['bf:note']
        self.assertEqual(3, len(bf_note))

    def test_implemented(self):
        entry = self.model_provider.get_entry(german_abstract=True, english_abstract=True, french_abstract=False)
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        translation = translator.translate_data(entry)
        # only check dynamic part
        translation = translator._extract_from_container(translation)
        bf_note: List[Dict] = translation['bf:note']
        self.assertEqual(2, len(bf_note))


class TranslateLanguageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_akan(self):
        entry = self.model_provider.get_entry(akan_language=True, german_language=False)
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        translation = translator.translate_data(entry)
        # only check dynamic part
        translation = translator._extract_from_container(translation)
        self.assertEqual(
            1,
            translation['dcterms:language'].__len__(),
        )

    def test_german(self):
        entry = self.model_provider.get_entry(german_language=True, akan_language=False)
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        translation = translator.translate_data(entry)
        # only check dynamic part
        translation = translator._extract_from_container(translation)
        self.assertEqual(
            1,
            translation['dcterms:language'].__len__(),
        )

    def test_akan_and_german(self):
        entry = self.model_provider.get_entry(german_language=True, akan_language=True)
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        translation = translator.translate_data(entry)
        # only check dynamic part
        translation = translator._extract_from_container(translation)
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
        controller = DefaultArchiveController(
            user=self.model_provider.user,
            media_objects={
                media,
            },
        )
        archiver: 'PhaidraArchiver' = controller.archiver
        metadata_data_archiver: 'DefaultMetadataArchiver' = archiver.metadata_data_archiver
        self.assertIsInstance(metadata_data_archiver, DefaultMetadataArchiver)
        self.assertIsInstance(metadata_data_archiver.schema, PhaidraMetaData)
        self.assertIsInstance(
            metadata_data_archiver.schema.fields['metadata'].nested.fields['json_ld'].nested,
            PhaidraContainer,
        )
        self.assertIsInstance(metadata_data_archiver.translator, PhaidraMetaDataTranslator)

    def test_entry_not_thesis_type(self):
        """Should return no default type."""
        entry = self.model_provider.get_entry(type_=True, thesis_type=False)
        media = self.model_provider.get_media(entry)
        controller = DefaultArchiveController(
            user=self.model_provider.user,
            media_objects={
                media,
            },
        )
        archiver: 'PhaidraArchiver' = controller.archiver
        metadata_data_archiver: 'DefaultMetadataArchiver' = archiver.metadata_data_archiver
        self.assertIsInstance(metadata_data_archiver, DefaultMetadataArchiver)
        self.assertIsInstance(metadata_data_archiver.schema, PhaidraMetaData)
        self.assertIsInstance(
            metadata_data_archiver.schema.fields['metadata'].nested.fields['json_ld'].nested,
            PhaidraContainer,
        )
        self.assertIsInstance(metadata_data_archiver.translator, PhaidraMetaDataTranslator)

    def test_entry_thesis_type(self):
        """Should return no thesis type."""
        entry = self.model_provider.get_entry(type_=True, thesis_type=True)
        media = self.model_provider.get_media(entry)
        controller = DefaultArchiveController(
            user=self.model_provider.user,
            media_objects={
                media,
            },
        )
        archiver: 'PhaidraArchiver' = controller.archiver
        metadata_data_archiver: 'ThesisMetadataArchiver' = archiver.metadata_data_archiver
        self.assertIsInstance(metadata_data_archiver, ThesisMetadataArchiver)
        self.assertIsInstance(metadata_data_archiver.schema, PhaidraThesisMetaData)
        self.assertIsInstance(
            metadata_data_archiver.schema.fields['metadata'].nested.fields['json_ld'].nested,
            PhaidraThesisContainer,
        )
        self.assertIsInstance(metadata_data_archiver.translator, PhaidraThesisMetaDataTranslator)


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
        archiver = ThesisMetadataArchiver(
            ArchiveObject(user=self.model_provider.user, entry=entry, media_objects={media})
        )
        archiver.validate()
        data = archiver.data['metadata']['json-ld']
        self.assertIn('dce:title', data)
        self.assertEqual(1, data['dce:title'].__len__())
        self.assertEqual(data['dce:title'], self.expected_title)

    def test_title_generation_from_not_thesis(self):
        entry = self.model_provider.get_entry(thesis_type=False)
        media = self.model_provider.get_media(entry=entry)
        archiver = DefaultMetadataArchiver(
            ArchiveObject(user=self.model_provider.user, entry=entry, media_objects={media})
        )
        archiver.validate()
        data = archiver.data['metadata']['json-ld']
        self.assertIn('dce:title', data)
        self.assertEqual(1, data['dce:title'].__len__())
        self.assertEqual(data['dce:title'], self.expected_title)


class AllDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()

    def test_incorrect_data_thesis(self):
        entry = self.model_provider.get_entry(author=False, type_=True, thesis_type=True)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        translator = PhaidraThesisMetaDataTranslator(mapping)
        schema = create_dynamic_phaidra_thesis_meta_data_schema(mapping)
        phaidra_data = translator.translate_data(entry)
        phaidra_errors = schema.validate(phaidra_data)
        errors = translator.translate_errors(phaidra_errors)
        self.assertEqual(
            errors,
            {
                'data': {
                    'authors': [
                        MISSING_AUTHOR,
                    ],
                }
            },
        )

    def test_upper_level_keys_create_default(self):
        entry = self.model_provider.get_entry(type_=False, thesis_type=False)
        archiver = DefaultMetadataArchiver(
            ArchiveObject(entry=entry, media_objects=set(), user=self.model_provider.user)
        )
        archiver.validate()
        phaidra_data = archiver.data
        self.assertEqual(list(phaidra_data.keys()), ['metadata'])
        self.assertEqual(list(phaidra_data['metadata'].keys()), ['json-ld'])

    def test_upper_level_keys_update_default(self):
        # Create entry and pus it to archive
        entry = self.model_provider.get_entry(type_=False, thesis_type=False)
        archiver = DefaultMetadataArchiver(
            ArchiveObject(entry=entry, media_objects=set(), user=self.model_provider.user)
        )
        archiver.push_to_archive()
        # Simulate update
        entry.refresh_from_db()
        archiver = DefaultMetadataArchiver(
            ArchiveObject(entry=entry, media_objects=set(), user=self.model_provider.user)
        )
        archiver.validate()
        phaidra_data = archiver.data
        self.assertEqual(list(phaidra_data.keys()), ['metadata'])
        self.assertEqual(list(phaidra_data['metadata'].keys()), ['json-ld'])

    def test_upper_level_keys_create_thesis(self):
        entry = self.model_provider.get_entry()
        archiver = ThesisMetadataArchiver(
            ArchiveObject(entry=entry, media_objects=set(), user=self.model_provider.user)
        )
        archiver.validate()
        phaidra_data = archiver.data
        self.assertEqual(list(phaidra_data.keys()), ['metadata'])
        self.assertEqual(list(phaidra_data['metadata'].keys()), ['json-ld'])

    def test_upper_level_keys_update_thesis(self):
        # Create entry and pus it to archive
        entry = self.model_provider.get_entry(thesis_type=True)
        archiver = ThesisMetadataArchiver(
            ArchiveObject(entry=entry, media_objects=set(), user=self.model_provider.user)
        )
        archiver.push_to_archive()
        # Simulate update
        entry.refresh_from_db()
        archiver = DefaultMetadataArchiver(
            ArchiveObject(entry=entry, media_objects=set(), user=self.model_provider.user)
        )
        archiver.validate()
        phaidra_data = archiver.data
        self.assertEqual(list(phaidra_data.keys()), ['metadata'])
        self.assertEqual(list(phaidra_data['metadata'].keys()), ['json-ld'])


class DynamicChildClassDoesNotInterfereWithSuperClass(TestCase):
    def test_dynamic_first(self):
        thesis_module = importlib.import_module(
            'media_server.archiver.implementations.phaidra.metadata.thesis.schemas'
        )
        entry = Entry()
        mapping = thesis_module.BidirectionalConceptsMapper.from_entry(entry)
        dynamic_schema = thesis_module.create_dynamic_phaidra_thesis_meta_data_schema(mapping)
        self.assertIsInstance(
            dynamic_schema.fields['metadata'].nested.fields['json_ld'].nested,
            PhaidraThesisContainer,
        )
        default_module = importlib.import_module(
            'media_server.archiver.implementations.phaidra.metadata.default.schemas'
        )
        static_schema = default_module.PhaidraMetaData()
        self.assertIsInstance(
            static_schema.fields['metadata'].nested.fields['json_ld'].nested,
            PhaidraContainer,
        )
