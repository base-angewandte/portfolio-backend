"""https://basedev.uni-ak.ac.at/redmine/issues/1419."""
from copy import deepcopy
from typing import Dict, List, Optional

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.datatranslation import (
    DCTitleTranslator,
    EdmHasTypeTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.schemas import DceTitleSchema, TypeLabelMatchSchema


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

    _example_type_data = {
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
                type=self._example_type_data,
            )
            self._entry.clean_fields()
            self._entry.save()
        return self._entry

    def test_translate_data(self):
        entry = self.entry
        translated_data = EdmHasTypeTranslator().translate_data(entry)
        self.assertEqual(translated_data, self.expected_translated_data)

    def test_validate_data(self):
        schema = TypeLabelMatchSchema()
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
        schema = TypeLabelMatchSchema()
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
