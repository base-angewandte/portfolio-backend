"""Test entry archival with no assets.

This is not part of the feature set, but it is a base functionality and
worth to test. However it can not be done with the api, since no assets
are not allowed there and so this test file will use the internal API.
"""

import django_rq
import requests

from django.core.validators import URLValidator
from django.test import TestCase

from media_server.archiver.implementations.phaidra.metadata.archiver import ThesisMetadataArchiver
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider
from media_server.archiver.interface.archiveobject import ArchiveObject


class CreateEntryTestCase(TestCase):
    def setUp(self) -> None:
        model_provider = ModelProvider()
        self.entry = model_provider.get_entry(thesis_type=True)
        thesis_archiver = ThesisMetadataArchiver(
            ArchiveObject(entry=self.entry, media_objects=set(), user=model_provider.user)
        )
        thesis_archiver.push_to_archive()
        self.entry.refresh_from_db()
        self.metadata = thesis_archiver.data

    def test_valid_archive_id_in_db(self):
        self.assertRegex(self.entry.archive_id, r'o:\d+')

    def test_valid_archive_uri_in_db(self):
        validator = URLValidator()
        self.assertIsNone(validator(self.entry.archive_URI))
        self.assertEqual(200, requests.get(self.entry.archive_URI).status_code)

    def test_phaidra_view_successful(self):
        response = requests.get(self.entry.archive_URI)
        self.assertEqual(response.url, f'https://phaidra-sandbox.univie.ac.at/view/{self.entry.archive_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.entry.title, response.text)
        self.assertIn(self.entry.archive_id, response.text)
        self.assertIn('Members (0)', response.text)

    def test_phaidra_meta_data_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/jsonld'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.metadata['metadata']['json-ld'])

    def test_phaidra_index_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/index'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('status', response_data)
        self.assertEqual(response_data['status'], 200)
        self.assertIn('index', response_data)
        index = response_data['index']
        self.assertIn('dc_identifier', index)
        self.assertEqual(
            index['dc_identifier'],
            [
                self.entry.archive_URI,
            ],
        )

    def test_phaidra_non_related(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/related'
        )
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data, {'alerts': [{'msg': 'Undefined relation', 'type': 'danger'}]})


class UpdateEntryTestCase(TestCase):
    def setUp(self) -> None:
        model_provider = ModelProvider()

        # First time

        self.entry = model_provider.get_entry(thesis_type=True)
        thesis_archiver = ThesisMetadataArchiver(
            ArchiveObject(entry=self.entry, media_objects=set(), user=model_provider.user)
        )
        thesis_archiver.push_to_archive()
        self.entry.refresh_from_db()
        self.create_archive_id = self.entry.archive_id
        self.metadata = thesis_archiver.data

        # Update
        self.new_title = 'I changed my mind'
        self.entry.title = self.new_title
        thesis_archiver = ThesisMetadataArchiver(
            ArchiveObject(entry=self.entry, media_objects=set(), user=model_provider.user)
        )
        thesis_archiver.push_to_archive()
        worker = django_rq.get_worker('high')
        worker.work(burst=True)
        self.entry.refresh_from_db()
        self.metadata = thesis_archiver.data

    def test_valid_archive_id_in_db(self):
        self.assertRegex(self.entry.archive_id, r'o:\d+')
        self.assertEqual(self.entry.archive_id, self.create_archive_id, 'archive_id should not change after update')

    def test_valid_archive_uri_in_db(self):
        validator = URLValidator()
        self.assertIsNone(validator(self.entry.archive_URI))
        self.assertEqual(200, requests.get(self.entry.archive_URI).status_code)

    def test_phaidra_view_successful(self):
        response = requests.get(self.entry.archive_URI)
        self.assertEqual(response.url, f'https://phaidra-sandbox.univie.ac.at/view/{self.entry.archive_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.new_title,
            response.text,
            f'new title "{self.new_title}" should be here'
            f' https://phaidra-sandbox.univie.ac.at/view/{self.entry.archive_id}',
        )

    def test_phaidra_meta_data_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/jsonld'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data, self.metadata['metadata']['json-ld'])
        self.assertEqual(self.new_title, response_data['dce:title'][0]['bf:mainTitle'][0]['@value'])

    def test_phaidra_index_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/index'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('status', response_data)
        self.assertEqual(response_data['status'], 200)
        self.assertIn('index', response_data)
        index = response_data['index']
        self.assertIn('dc_identifier', index)
        self.assertEqual(
            index['dc_identifier'],
            [
                self.entry.archive_URI,
            ],
        )

    def test_phaidra_non_related(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/related'
        )
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data, {'alerts': [{'msg': 'Undefined relation', 'type': 'danger'}]})
