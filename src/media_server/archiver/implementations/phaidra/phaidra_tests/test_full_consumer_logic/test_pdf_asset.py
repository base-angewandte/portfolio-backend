from pathlib import Path

import django_rq
import requests
from django.conf import settings

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.test import TestCase

from core.models import Entry
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
        - create media with pdf file
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
        cls.media.type = 'd'  # auto detection does not work here, unknown reason
        cls.media.save()
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()
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
            message = f'validation_error={validation_error}' \
                      f'self.media.archive_URI={self.media.archive_URI}' \
                      f'self.media.archive_URI.__class__={self.media.archive_URI.__class__}'
        self.assertTrue(url_valid, message)
        self.assertEqual(200, requests.get(self.media.archive_URI).status_code)

    def test_valid_media_archive_status_in_db(self):
        self.assertEqual(STATUS_ARCHIVED, self.media.archive_status)

    def test_phaidra_entry_view_successful(self):
        response = requests.get(self.entry.archive_URI)
        self.assertEqual(response.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.entry.archive_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.entry.title, response.text,
                      f'self.entry.title={self.entry.title} not found in {response.url}'
                      )
        self.assertIn(self.entry.archive_id, response.text,
                      f'self.entry.archive_id={self.entry.archive_id} not found in {response.url}'
                      )

    def test_phaidra_media_view_successful(self):
        response = requests.get(self.media.archive_URI)
        self.assertEqual(response.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.media.archive_id}')
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
        self.assertEqual(data['metadata']['JSON-LD']['ebucore:filename'][0], Path(self.media.file.name).name)

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


class ArchiveEntryWithTwoPdfFiles(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        - Create an entry
        - create 2 media with pdf file
        - connect the media to entry
        - send a request to the API to archival it
        - fast forward the redis queue for sync testing
        - reload data from db for testing
        - generate metadata for testing
        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()
        cls.media_1 = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        cls.media_1.type = 'd'
        cls.media_1.save()
        cls.media_2 = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        cls.media_2.type = 'd'
        cls.media_2.save()
        client_provider = ClientProvider(model_provider)
        client_provider.get_multiple_medias_primary_key_response({cls.media_1, cls.media_2}, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.entry.refresh_from_db()
        cls.media_1.refresh_from_db()
        cls.media_2.refresh_from_db()
        archiver = ThesisMetadataArchiver(
            archive_object=ArchiveObject(
                entry=cls.entry, user=model_provider.user, media_objects={cls.media_1, cls.media_2}
            )
        )
        archiver.validate()
        cls.metadata = archiver.data

    def test_valid_entry_archive_id_in_db(self):
        self.assertRegex(self.entry.archive_id, r'o:\d+')

    def test_valid_media_archive_id_in_db(self):
        self.assertRegex(self.media_1.archive_id, r'o:\d+')
        self.assertRegex(self.media_2.archive_id, r'o:\d+')

    def test_valid_entry_archive_uri_in_db(self):
        validator = URLValidator()
        self.assertIsNone(validator(self.entry.archive_URI))
        self.assertEqual(200, requests.get(self.entry.archive_URI).status_code)

    def test_valid_media_archive_uri_in_db(self):
        validator = URLValidator()
        # Have not found a "assertDoesNotRaise method so …
        try:
            validator(self.media_1.archive_URI)
            url_valid = True
            message = 'everything ok'
        except ValidationError as validation_error:
            url_valid = False
            message = f'validation_error={validation_error} ' \
                      f'self.media_1.archive_URI=={self.media_1.archive_URI}' \
                      f'self.media_1.archive_URI.__class__=={self.media_1.archive_URI.__class__}'
        self.assertTrue(url_valid, message)
        self.assertEqual(200, requests.get(self.media_1.archive_URI).status_code)
        try:
            validator(self.media_2.archive_URI)
            url_valid = True
            message = 'everything ok'
        except ValidationError as validation_error:
            url_valid = False
            message = f'validation_error={validation_error}' \
                      f'self.media_2.archive_URI={self.media_2.archive_URI} ' \
                      f'self.media_2.archive_URI.__class__={self.media_2.archive_URI.__class__}'
        self.assertTrue(url_valid, message)
        self.assertEqual(200, requests.get(self.media_2.archive_URI).status_code)

    def test_valid_media_archive_status_in_db(self):
        self.assertEqual(STATUS_ARCHIVED, self.media_1.archive_status)
        self.assertEqual(STATUS_ARCHIVED, self.media_2.archive_status)

    def test_phaidra_entry_view_successful(self):
        response = requests.get(self.entry.archive_URI)
        self.assertEqual(response.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.entry.archive_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.entry.title, response.text,
                      f'self.entry.title={self.entry.title} not found in {response.url}'
                      )
        self.assertIn(self.entry.archive_id, response.text, f'self.entry.archive_id={self.entry.archive_id} '
                                                            f'not found in {response.url}')

    def test_phaidra_media_view_successful(self):
        response_1 = requests.get(self.media_1.archive_URI)
        self.assertEqual(response_1.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.media_1.archive_id}')
        self.assertEqual(response_1.status_code, 200)
        response_2 = requests.get(self.media_2.archive_URI)
        self.assertEqual(response_2.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.media_2.archive_id}')
        self.assertEqual(response_2.status_code, 200)

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
        response_1 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_1.archive_id}/metadata'
        )
        data_1 = response_1.json()
        self.assertEqual(data_1['status'], 200)
        self.assertEqual(data_1['metadata']['JSON-LD']['ebucore:filename'][0], Path(self.media_1.file.name).name)

        response_2 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_2.archive_id}/metadata'
        )
        data_2 = response_2.json()
        self.assertEqual(data_2['status'], 200)
        self.assertEqual(data_2['metadata']['JSON-LD']['ebucore:filename'][0], Path(self.media_2.file.name).name)

    def test_phaidra_entry_index_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/index'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        members = set(data['index']['hasmember'])
        self.assertEqual(members, {self.media_1.archive_id, self.media_2.archive_id})

    def test_phaidra_media_index_successful(self):
        response_1 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_1.archive_id}/index'
        )
        data_1 = response_1.json()
        self.assertEqual(data_1['status'], 200)
        self.assertEqual(data_1['index']['ismemberof'][0], self.entry.archive_id)

        response_2 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_2.archive_id}/index'
        )
        data_2 = response_2.json()
        self.assertEqual(data_2['status'], 200)
        self.assertEqual(data_2['index']['ismemberof'][0], self.entry.archive_id)


class AddOnePdfFileToEntryWithOnePdfFile(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        - Create an entry
        - create media with pdf file
        - connect the media to entry
        - send a request to the API to archival it
        - fast forward the redis queue for sync testing
        - create another media with pdf file
        - connect it to entry
        - update archival
        - reload data from db for testing
        - generate metadata for testing
        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()

        cls.media_1 = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        cls.media_1.type = 'd'  # auto detection does not work here, unknown reason
        cls.media_1.save()
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media_1, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done

        cls.entry.refresh_from_db()
        cls.first_entry_archive_id = cls.entry.archive_id
        cls.media_1.refresh_from_db()
        cls.first_media_archive_id = cls.media_1.archive_id

        cls.media_2 = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        cls.media_2.type = 'd'  # auto detection does not work here, unknown reason
        cls.media_2.save()
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media_2, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done

        cls.entry.refresh_from_db()
        cls.media_1.refresh_from_db()
        cls.media_2.refresh_from_db()
        archiver = ThesisMetadataArchiver(
            archive_object=ArchiveObject(entry=cls.entry, user=model_provider.user, media_objects={cls.media_2})
        )
        archiver.validate()
        cls.metadata = archiver.data

    def test_entry_archive_id_constant(self):
        self.assertEqual(self.entry.archive_id, self.first_entry_archive_id)

    def test_valid_media_archive_ids_in_db(self):
        self.assertEqual(self.media_1.archive_id, self.first_media_archive_id)
        self.assertRegex(self.media_2.archive_id, r'o:\d+')
        self.assertNotEqual(self.media_1.archive_id, self.media_2.archive_id)

    def test_valid_entry_archive_uri_in_db(self):
        validator = URLValidator()
        self.assertIsNone(validator(self.entry.archive_URI))
        self.assertEqual(200, requests.get(self.entry.archive_URI).status_code)

    def test_valid_media_1_archive_uri_in_db(self):
        validator = URLValidator()
        # Have not found a "assertDoesNotRaise method so …
        try:
            validator(self.media_1.archive_URI)
            url_valid = True
            message = 'everything ok'
        except ValidationError as validation_error:
            url_valid = False
            message = f'validation_error={validation_error} ' \
                      f'self.media_1.archive_URI={self.media_1.archive_URI} ' \
                      f'self.media_1.archive_URI.__class__={self.media_1.archive_URI.__class__}'
        self.assertTrue(url_valid, message)
        self.assertEqual(200, requests.get(self.media_1.archive_URI).status_code)

    def test_valid_media_2_archive_uri_in_db(self):
        validator = URLValidator()
        # Have not found a "assertDoesNotRaise method so …
        try:
            validator(self.media_2.archive_URI)
            url_valid = True
            message = 'everything ok'
        except ValidationError as validation_error:
            url_valid = False
            message = f'validation_error={validation_error} ' \
                      f'self.media_2.archive_URI={self.media_2.archive_URI} ' \
                      f'self.media_2.archive_URI.__class__={self.media_2.archive_URI.__class__}'
        self.assertTrue(url_valid, message)
        self.assertEqual(200, requests.get(self.media_2.archive_URI).status_code)

    def test_valid_media_archive_status_in_db(self):
        self.assertEqual(STATUS_ARCHIVED, self.media_1.archive_status)
        self.assertEqual(STATUS_ARCHIVED, self.media_2.archive_status)

    def test_phaidra_entry_view_successful(self):
        response = requests.get(self.entry.archive_URI)
        self.assertEqual(response.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.entry.archive_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.entry.title, response.text,
                      f'self.entry.title={self.entry.title} not found in {response.url}'
                      )
        self.assertIn(self.entry.archive_id, response.text,
                      f'self.entry.archive_id={self.entry.archive_id} not found in {response.url}'
                      )

    def test_phaidra_media_1_view_successful(self):
        response = requests.get(self.media_1.archive_URI)
        self.assertEqual(response.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.media_1.archive_id}')
        self.assertEqual(response.status_code, 200)

    def test_phaidra_media_2_view_successful(self):
        response = requests.get(self.media_2.archive_URI)
        self.assertEqual(response.url, f'{settings.ARCHIVE_URIS["IDENTIFIER_BASE_TESTING"]}detail/{self.media_2.archive_id}')
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
        response_1 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_1.archive_id}/metadata'
        )
        data_1 = response_1.json()
        self.assertEqual(data_1['status'], 200)
        self.assertEqual(data_1['metadata']['JSON-LD']['ebucore:filename'][0], Path(self.media_1.file.name).name)

        response_2 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_2.archive_id}/metadata'
        )
        data_2 = response_2.json()
        self.assertEqual(data_2['status'], 200)
        self.assertEqual(data_2['metadata']['JSON-LD']['ebucore:filename'][0], Path(self.media_2.file.name).name)

    def test_phaidra_entry_index_successful(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/index'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        members = set(data['index']['hasmember'])
        self.assertEqual(members, {self.media_1.archive_id, self.media_2.archive_id})

    def test_phaidra_media_index_successful(self):
        response_1 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_1.archive_id}/index'
        )
        data_1 = response_1.json()
        self.assertEqual(data_1['status'], 200)
        self.assertEqual(data_1['index']['ismemberof'][0], self.entry.archive_id)

        response_2 = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media_2.archive_id}/index'
        )
        data_2 = response_2.json()
        self.assertEqual(data_2['status'], 200)
        self.assertEqual(data_2['index']['ismemberof'][0], self.entry.archive_id)


class UpdateEntryWithOnePdfFile(TestCase):
    new_title = 'new title'

    @classmethod
    def setUpTestData(cls):
        """
        - Create an entry
        - create media with pdf file
        - connect the media to entry
        - send a request to the API to archival it
        - fast forward the redis queue for sync testing
        - change entry title, save
        - do update of archival
        - fast forward the redis queue for sync testing
        - reload data from db for testing
        - generate metadata for testing

        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()
        cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        cls.media.type = 'd'  # auto detection does not work here, unknown reason
        cls.media.save()
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.entry = Entry.objects.get(pk=cls.entry.id)
        cls.entry.title = cls.new_title
        cls.entry.save()
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()
        client_provider.get_update_entry_archival_response(cls.entry)
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        archiver = ThesisMetadataArchiver(
            archive_object=ArchiveObject(entry=cls.entry, user=model_provider.user, media_objects={cls.media})
        )
        archiver.validate()
        cls.metadata = archiver.data

    def test_phaidra_entry_meta_data_changed(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/metadata'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        self.assertEqual(
            self.new_title,
            response.json()['metadata']['JSON-LD']['dce:title'][0]['bf:mainTitle'][0]['@value'],
            f'Did not find expected title in '
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/metadata',
        )

    def test_phaidra_entry_index_still_valid(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/index'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['index']['hasmember'][0], self.media.archive_id)

    def test_phaidra_media_index_still_valid(self):
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media.archive_id}/index'
        )
        data = response.json()
        self.assertEqual(data['status'], 200)
        self.assertEqual(data['index']['ismemberof'][0], self.entry.archive_id)
