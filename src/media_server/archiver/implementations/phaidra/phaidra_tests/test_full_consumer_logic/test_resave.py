"""https://basedev.uni-ak.ac.at/redmine/issues/1503.

>  archive_id and archive_URI fields are deleted from the database

after changing / resaving the database
"""
from json import dumps

import django_rq
from rest_framework.test import APITestCase

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Entry
from media_server.archiver.implementations.phaidra.phaidra_tests.utilities import create_random_test_password
from media_server.models import Media

license_copyright = {
    'source': 'http://base.uni-ak.ac.at/portfolio/licenses/copyright',
    'label': {
        'de': 'urheberrechtlich geschützt',
        'en': 'Copyright',
    },
}


class OnePdfResaved(APITestCase):
    def setUp(self) -> None:
        """(Log in as a user)

        Create an entry with the web api,
        attach a file with the web api,
        archive the file with the web api,
        change the entry with the web api,
        :return:
        """
        pw = create_random_test_password()
        User.objects.create_user(username='test_user', password=pw)
        client = self.client
        client.login(username='test_user', password=pw)

        # Create an entry …
        response = self.client.post('/api/v1/entry/', data={'title': 'Test'})
        entry_id = response.data['id']

        # attach a file …
        response = client.post(
            '/api/v1/media/',
            data={
                'file': SimpleUploadedFile('example.pdf', b'example file'),
                'entry': entry_id,
                'published': 'false',
                'license': dumps(license_copyright),
            },
        )
        media_id = response.data
        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done

        # archive
        response = client.get(
            f'/api/v1/archive_assets/media/{media_id}/',
        )
        archive_id = response.data['object']
        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done

        # change entry
        response = client.put(
            f'/api/v1/entry/{entry_id}/',
            data={
                'title': 'Test',
                'type': {
                    'label': {'de': 'Album', 'en': 'Album'},
                    'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/album',
                },
            },
            format='json',
        )

        # byby ;-)
        client.logout()
        # store data for tests
        self.entry_id = entry_id
        self.archive_id = archive_id
        self.media_id = media_id

    def test_entry_has_archive_id(self):
        entry = Entry.objects.get(pk=self.entry_id)
        self.assertIsNotNone(entry.archive_id)

    def test_entry_has_correct_archive_id(self):
        entry = Entry.objects.get(pk=self.entry_id)
        self.assertEqual(entry.archive_id, self.archive_id)

    def test_entry_has_archive_time(self):
        entry = Entry.objects.get(pk=self.entry_id)
        self.assertIsNotNone(entry.archive_date)

    def test_media_has_archive_id(self):
        media = Media.objects.get(pk=self.media_id)
        self.assertIsNotNone(media.archive_id)

    def test_media_has_archive_time(self):
        media = Media.objects.get(pk=self.media_id)
        self.assertIsNotNone(media.archive_date)


class OnePdfResavedWithArchiveIDSetNull(APITestCase):
    """Client accidentally sets the archive id to null."""

    def setUp(self) -> None:
        """(Log in as a user)

        Create an entry with the web api,
        attach a file with the web api,
        archive the file with the web api,
        change the entry with the web api,
        :return:
        """
        pw = create_random_test_password()
        User.objects.create_user(username='test_user', password=pw)
        client = self.client
        client.login(username='test_user', password=pw)

        # Create an entry …
        response = self.client.post('/api/v1/entry/', data={'title': 'Test'})
        entry_id = response.data['id']

        # attach a file …
        response = client.post(
            '/api/v1/media/',
            data={
                'file': SimpleUploadedFile('example.pdf', b'example file'),
                'entry': entry_id,
                'published': 'false',
                'license': dumps(license_copyright),
            },
        )
        media_id = response.data
        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done

        # archive
        response = client.get(
            f'/api/v1/archive_assets/media/{media_id}/',
        )
        archive_id = response.data['object']
        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done

        # change entry
        response = client.put(
            f'/api/v1/entry/{entry_id}/',
            data={
                'title': 'Test',
                'archive_id': None,
                'type': {
                    'label': {'de': 'Album', 'en': 'Album'},
                    'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/album',
                },
            },
            format='json',
        )

        # byby ;-)
        client.logout()
        # store data for tests
        self.entry_id = entry_id
        self.archive_id = archive_id
        self.media_id = media_id

    def test_entry_has_archive_id(self):
        entry = Entry.objects.get(pk=self.entry_id)
        self.assertIsNotNone(entry.archive_id)

    def test_entry_has_correct_archive_id(self):
        entry = Entry.objects.get(pk=self.entry_id)
        self.assertEqual(entry.archive_id, self.archive_id)

    def test_entry_has_archive_time(self):
        entry = Entry.objects.get(pk=self.entry_id)
        self.assertIsNotNone(entry.archive_date)

    def test_media_has_archive_id(self):
        media = Media.objects.get(pk=self.media_id)
        self.assertIsNotNone(media.archive_id)

    def test_media_has_archive_time(self):
        media = Media.objects.get(pk=self.media_id)
        self.assertIsNotNone(media.archive_date)
