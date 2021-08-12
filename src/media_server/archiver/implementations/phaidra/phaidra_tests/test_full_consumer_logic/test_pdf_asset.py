import django_rq
import requests

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.test import TestCase

from media_server.archiver import STATUS_ARCHIVED
from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.implementations.phaidra.metadata.archiver import ThesisMetadataArchiver
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ClientProvider, ModelProvider
from media_server.archiver.interface.archiveobject import ArchiveObject


class ArchiveEntryWithOnePdfFile(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        - Create an entry
        - create media with text file
        - connect the media to entry
        - send a request to the API to archival it
        - fast forward the redis queue for sync testing
        - reload data from db for testing
        - generate metadata for testing
        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()
        cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        cls.media.type = 'd'
        cls.media.save()
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()
        # create m
        archiver = ThesisMetadataArchiver(
            archive_object=ArchiveObject(entry=cls.entry, user=model_provider.user, media_objects={cls.media})
        )
        archiver.validate()
        cls.metadata = archiver.data

    def test_valid_entry_archive_id_in_db(self):
        self.assertRegex(self.entry.archive_id, r'o:\d+')

    def test_valid_media_archive_id_in_db(self):
        self.assertRegex(self.media.archive_id, r'o:\d+')

    def test_valid_entry_archive_uri_in_db(self):
        validator = URLValidator()
        self.assertIsNone(validator(self.entry.archive_URI))
        self.assertEqual(200, requests.get(self.entry.archive_URI).status_code)

    def test_valid_media_archive_uri_in_db(self):
        validator = URLValidator()
        # Have not found a "assertDoesNotRaise method so …
        try:
            validator(self.media.archive_URI)
            url_valid = True
            message = 'everything ok'
        except ValidationError as validation_error:
            url_valid = False
            message = f'{validation_error=} {self.media.archive_URI=} {self.media.archive_URI.__class__=}'
        self.assertTrue(url_valid, message)
        self.assertEqual(200, requests.get(self.media.archive_URI).status_code)

    def test_valid_media_archive_status_in_db(self):
        self.assertEqual(STATUS_ARCHIVED, self.media.archive_status)

    def test_phaidra_entry_view_successful(self):
        response = requests.get(self.entry.archive_URI)
        self.assertEqual(response.url, f'https://phaidra-sandbox.univie.ac.at/view/{self.entry.archive_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.entry.title, response.text, f'{self.entry.title=} not found in {response.url}')
        self.assertIn(self.entry.archive_id, response.text, f'{self.entry.archive_id=} not found in {response.url}')

    def test_phaidra_media_view_successful(self):
        response = requests.get(self.media.archive_URI)
        self.assertEqual(response.url, f'https://phaidra-sandbox.univie.ac.at/view/{self.media.archive_id}')
        self.assertEqual(response.status_code, 200)

    def test_phaidra_entry_meta_data_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/metadata'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        self.assertEqual(
            self.metadata['metadata']['json-ld'],
            response.json()['metadata']['JSON-LD'],
            f'Did not find expected metadata in '
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/metadata',
        )

    def test_phaidra_media_meta_data_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media.archive_id}/metadata'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['metadata']['JSON-LD']['ebucore:filename'][0], self.media.file.name)

    def test_phaidra_entry_index_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/index'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['index']['hasmember'][0], self.media.archive_id)

    def test_phaidra_media_index_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media.archive_id}/index'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['index']['ismemberof'][0], self.entry.archive_id)
