"""https://basedev.uni-ak.ac.at/redmine/issues/1419."""
import unittest
from typing import Dict, List

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.datatranslation import DCTitleTranslator
from media_server.archiver.implementations.phaidra.metadata.schemas import DceTitleSchema


class MetaDataTitle(unittest.TestCase):
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
        self.assertEqual(phaidra_errors, {})
        portfolio_errors = self._only_title_error_transformation(phaidra_errors)
        self.assertEqual(portfolio_errors, {})

    def test_only_subtitle_data_flow(self):
        entry = Entry(subtitle=self._subtitle)
        phaidra_data = self._only_subtitle_data_transformation(entry)
        self.assertIs(phaidra_data.__class__, list)  # detailed test in _method
        phaidra_errors = self._only_subtitle_validation(phaidra_data)
        self.assertEqual(len(phaidra_errors), 1)
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

    def _only_title_validation(self, data: List) -> Dict:
        schema = DceTitleSchema()
        errors = [schema.validate(datum) for datum in data]
        errors = errors.pop()
        self.assertEqual(errors, {})
        return errors

    def _only_subtitle_validation(self, data: List) -> Dict:
        self.assertEqual(
            data.__len__(), 1, 'if data is not length 1, this test does not makes sense. Data should be default 1'
        )  # !
        schema = DceTitleSchema()
        errors: List = [schema.validate(datum) for datum in data]
        errors: dict = errors.pop()
        self.assertEqual(
            errors,
            {
                'bf:mainTitle': {
                    0: {
                        '@value': ['Missing data for required field.'],
                    }
                }
            },
        )
        return errors

    def _only_title_error_transformation(self, errors: Dict) -> Dict:
        translator = DCTitleTranslator()
        portfolio_errors = translator.translate_errors(errors)
        self.assertEqual(portfolio_errors, {})
        return errors

    def _only_subtitle_error_transformation(self, errors: Dict) -> Dict:
        translator = DCTitleTranslator()
        portfolio_errors = translator.translate_errors(errors)
        self.assertEqual(
            portfolio_errors,
            {
                'title': ['Missing data for required field.'],
            },
        )
        return errors
