"""https://basedev.uni-ak.ac.at/redmine/issues/1419."""
from copy import deepcopy
from typing import Dict, List, Optional

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.datatranslation import (
    DcTermsSubjectTranslator,
    DCTitleTranslator,
    EdmHasTypeTranslator,
    GenericSkosConceptTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.schemas import DceTitleSchema, SkosConceptSchema


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
        translated_errors = EdmHasTypeTranslator().translate_errors(errors)
        # None of these errors are user relevant, they would be by programmers fault
        self.assertEqual(
            translated_errors,
            [
                {},
            ],
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


class DcTermsSubjectTestCase(TestCase):
    example_input_keywords = [
        {
            'label': {'de': 'Airbrush', 'en': 'Airbrushing'},
            'source': 'http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e',
        }
    ]

    expected_translated_data = [
        {
            '@type': 'skos:Concept',
            'skos:exactMatch': ['http://base.uni-ak.ac.at/recherche/keywords/c_699b3d9e'],
            'skos:prefLabel': [
                {'@value': 'Airbrush', '@language': 'deu'},
                {'@value': 'Airbrushing', '@language': 'eng'},
            ],
        }
    ]

    def test_translate_data(self):
        entry = Entry(keywords=self.example_input_keywords)
        self.assertEqual(DcTermsSubjectTranslator().translate_data(entry), self.expected_translated_data)

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
        del translated_datum['skos:prefLabel']
        schema = SkosConceptSchema()
        validation = schema.validate(translated_datum)
        self.assertEqual(
            validation,
            {
                'skos:prefLabel': {
                    0: {
                        '@language': ['Missing data for required field.'],
                        '@value': ['Missing data for required field.'],
                    }
                },
            },
        )

    def test_translate_errors(self):
        phaidra_errors = [
            {
                'skos:prefLabel': {
                    0: {
                        '@language': ['Missing data for required field.'],
                        '@value': ['Missing data for required field.'],
                    }
                },
            }
        ]
        portfolio_errors = DcTermsSubjectTranslator().translate_errors(phaidra_errors)
        self.assertEqual(
            portfolio_errors,
            [
                {},
            ],
        )

    def test_faulty_input_data(self):
        data = deepcopy(self.example_input_keywords)
        del data[0]['source']
        entry = Entry(keywords=data)
        self.assertRaises(RuntimeError, lambda: DcTermsSubjectTranslator().translate_data(entry))

    def test_empty_input_data(self):
        entry = Entry()
        self.assertRaises(RuntimeError, lambda: DcTermsSubjectTranslator().translate_data(entry))


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
