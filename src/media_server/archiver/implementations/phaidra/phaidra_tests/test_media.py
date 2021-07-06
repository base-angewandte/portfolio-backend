import unittest

from media_server.archiver.implementations.phaidra.media.datatranslation import PhaidraMediaDataTranslator
from media_server.archiver.implementations.phaidra.media.schemas import PhaidraMediaData
from media_server.models import Media


class PhaidraMediaDataTestCase(unittest.TestCase):

    phaidra_media_data_translator = PhaidraMediaDataTranslator()
    phaidra_media_data_validator = PhaidraMediaData()
    example_mime_type = 'audio/aac'
    example_file = 'some_file.aac'
    example_license = {'source': 'not-important'}

    def get_media_object(self, has_mime_type=True, has_file=True, has_license=True):
        kwargs = {
            'mime_type': self.example_mime_type if has_mime_type else None,
            'file': self.example_file if has_file else None,
            'license': self.example_license if has_license else None,
        }
        kwargs = {kwarg: value for kwarg, value in kwargs.items() if value}
        return Media(**kwargs)

    def test_data_translation(self):
        media = self.get_media_object()
        data = self.phaidra_media_data_translator.translate_data(media)
        self.assertEqual(
            data,
            {
                'metadata': {
                    'json-ld': {
                        'ebucore:hasMimeType': [
                            self.example_mime_type,
                        ],
                        'ebucore:filename': [self.example_file],
                        'edm:rights': [self.example_license['source']],
                    }
                }
            },
        )

    def test_data_translation_empty(self):
        """
        Test, that empty data translation does not run into errors: validation is something else's concept
        :return:
        """
        media = self.get_media_object(has_mime_type=False, has_file=False, has_license=False)
        data = self.phaidra_media_data_translator.translate_data(media)
        self.assertEqual(
            data, {'metadata': {'json-ld': {'ebucore:hasMimeType': [], 'ebucore:filename': [], 'edm:rights': []}}}
        )

    def test_data_translation_missing_mime_type(self):
        media = self.get_media_object(has_mime_type=False)
        data = self.phaidra_media_data_translator.translate_data(media)
        self.assertEqual(
            data,
            {
                'metadata': {
                    'json-ld': {
                        'ebucore:hasMimeType': [],
                        'ebucore:filename': [self.example_file],
                        'edm:rights': [self.example_license['source']],
                    }
                }
            },
        )

    def test_data_translation_missing_file_name(self):
        media = self.get_media_object(has_file=False)
        data = self.phaidra_media_data_translator.translate_data(media)
        self.assertEqual(
            data,
            {
                'metadata': {
                    'json-ld': {
                        'ebucore:hasMimeType': [
                            self.example_mime_type,
                        ],
                        'ebucore:filename': [],
                        'edm:rights': [self.example_license['source']],
                    }
                }
            },
        )

    def test_data_translation_missing_license_source(self):
        media = self.get_media_object(has_license=False)
        data = self.phaidra_media_data_translator.translate_data(media)
        self.assertEqual(
            data,
            {
                'metadata': {
                    'json-ld': {
                        'ebucore:hasMimeType': [
                            self.example_mime_type,
                        ],
                        'ebucore:filename': [self.example_file],
                        'edm:rights': [],
                    }
                }
            },
        )

    def test_data_validation_ok(self):
        media = self.get_media_object()
        phaidra_data = self.phaidra_media_data_translator.translate_data(media)
        phaidra_errors = self.phaidra_media_data_validator.validate(phaidra_data)
        self.assertEqual(phaidra_errors, {})
        our_errors = self.phaidra_media_data_translator.translate_errors(phaidra_errors)
        self.assertEqual(our_errors, {})

    def test_missing_data_validation_missing_license_source(self):
        media = self.get_media_object(has_license=False)
        phaidra_data = self.phaidra_media_data_translator.translate_data(media)
        phaidra_errors = self.phaidra_media_data_validator.validate(phaidra_data)
        self.assertEqual(
            phaidra_errors,
            {
                'metadata': {
                    'json-ld': {
                        'edm:rights': [
                            'Shorter than minimum length 1.',
                        ],
                    }
                }
            },
        )
        our_errors = self.phaidra_media_data_translator.translate_errors(phaidra_errors)
        self.assertEqual(
            our_errors,
            {
                'media': {
                    'license': {
                        'source': [
                            'Shorter than minimum length 1.',
                        ],
                    }
                }
            },
        )

    def test_missing_all_data_validation(self):
        media = self.get_media_object(has_license=False, has_file=False, has_mime_type=False)
        phaidra_data = self.phaidra_media_data_translator.translate_data(media)
        phaidra_errors = self.phaidra_media_data_validator.validate(phaidra_data)
        self.assertEqual(
            phaidra_errors,
            {
                'metadata': {
                    'json-ld': {
                        'edm:rights': [
                            'Shorter than minimum length 1.',
                        ],
                        'ebucore:hasMimeType': [
                            'Shorter than minimum length 1.',
                        ],
                        'ebucore:filename': [
                            'Shorter than minimum length 1.',
                        ],
                    }
                }
            },
        )
