from typing import Optional

from django.test import TestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.media.archiver import MediaArchiver
from media_server.archiver.implementations.phaidra.media.datatranslation import PhaidraMediaDataTranslator
from media_server.archiver.implementations.phaidra.media.schemas import PhaidraMediaData
from media_server.archiver.implementations.phaidra.phaidra_tests.utilities import ModelProvider
from media_server.archiver.interface.archiveobject import ArchiveObject
from media_server.archiver.messages import validation as validation_messages
from media_server.archiver.messages.validation import MISSING_DATA_FOR_REQUIRED_FIELD
from media_server.models import Media


class PhaidraMediaDataTestCase(TestCase):
    phaidra_media_data_translator = PhaidraMediaDataTranslator()
    phaidra_media_data_validator = PhaidraMediaData()
    example_mime_type = 'audio/aac'
    example_file = 'some_file.aac'
    example_license = {'source': 'http://base.uni-ak.ac.at/portfolio/licenses/CC-BY-SA-4.0'}

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
                        'ebucore:filename': [self.example_file],
                        'edm:rights': [
                            'http://creativecommons.org/licenses/by-sa/4.0/',
                        ],
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
        self.assertEqual(data, {'metadata': {'json-ld': {'ebucore:filename': [], 'edm:rights': []}}})

    def test_data_translation_missing_mime_type(self):
        media = self.get_media_object(has_mime_type=False)
        data = self.phaidra_media_data_translator.translate_data(media)
        self.assertEqual(
            data,
            {
                'metadata': {
                    'json-ld': {
                        'ebucore:filename': [self.example_file],
                        'edm:rights': [
                            'http://creativecommons.org/licenses/by-sa/4.0/',
                        ],
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
                        'ebucore:filename': [],
                        'edm:rights': [
                            'http://creativecommons.org/licenses/by-sa/4.0/',
                        ],
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
                            MISSING_DATA_FOR_REQUIRED_FIELD,
                        ],
                    }
                }
            },
        )
        our_errors = self.phaidra_media_data_translator.translate_errors(phaidra_errors)
        self.assertEqual(
            our_errors,
            {'media': {'license': [validation_messages.MISSING_DATA_FOR_REQUIRED_FIELD]}},
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
                            MISSING_DATA_FOR_REQUIRED_FIELD,
                        ],
                        'ebucore:filename': [
                            MISSING_DATA_FOR_REQUIRED_FIELD,
                        ],
                    }
                }
            },
        )


class TestUpperDataStructure(TestCase):
    """https://basedev.uni-ak.ac.at/redmine/issues/1477."""

    entry: Optional['Entry'] = None
    model_provider: Optional['ModelProvider'] = None

    def setUp(self):
        """
        We need one entry, that has been archived yet
        :return:
        """
        self.model_provider = ModelProvider()
        self.entry = self.model_provider.get_entry(thesis_type=False)
        self.archive_object = ArchiveObject(
            entry=self.entry,
            media_objects=set(),  # nothing to here, since we test this,
            user=self.model_provider.user,
        )
        self.media = self.model_provider.get_media(self.entry)
        self.archive_object.media_objects.add(self.media)

    def test_data_is_object(self):
        archiver = MediaArchiver.from_archive_object(self.archive_object)
        archiver.validate()  # generates data
        self.assertIsInstance(archiver.data, dict)
