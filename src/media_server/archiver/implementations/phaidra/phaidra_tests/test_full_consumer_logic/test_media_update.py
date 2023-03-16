import json

import django_rq
import requests
from rest_framework.test import APITestCase

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Entry
from media_server.archiver.implementations.phaidra.phaidra_tests.utilities import ClientProvider, ModelProvider
from media_server.models import Media

from ..utilities import create_random_test_password


class OnePdfResaved(APITestCase):
    def setUp(self) -> None:
        """(Log in as a user)

        Create an entry with the web api,
        attach a file with the web api,
        archive the file with the web api,
        change the media with the web api,
        update archive with the web api
        :return:
        """
        pw = create_random_test_password()
        User.objects.create_user(username='test_user', password=pw)
        client = self.client
        client.login(username='test_user', password=pw)

        # define license_states for testing
        self.first_portfolio_license = 'http://base.uni-ak.ac.at/portfolio/licenses/copyright'
        self.second_portfolio_license = 'http://base.uni-ak.ac.at/portfolio/licenses/CC-BY-NC-4.0'
        self.second_phaidra_license = 'http://creativecommons.org/licenses/by-nc/4.0/'

        # Create an entry …
        response = client.post('/api/v1/entry/', data={'title': 'Test'})
        entry_id = response.data['id']

        # attach a file …
        response = client.post(
            '/api/v1/media/',
            data={
                'file': SimpleUploadedFile('example.pdf', b'example file'),
                'entry': entry_id,
                'published': 'false',
                'license': json.dumps(
                    {
                        'source': self.first_portfolio_license,
                        'label': {'de': 'urheberrechtlich geschützt', 'en': 'Copyright'},
                    }
                ),
            },
        )
        media_id = response.data
        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done

        # archive
        response = client.get(
            f'/api/v1/archive_assets/media/{media_id}/',
        )
        if response.status_code != 200:
            raise RuntimeError(f'testserver responded with code {response.status_code} and content {response.json()}')

        archive_id = response.data['object']
        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done

        # change media
        media = Media.objects.get(pk=media_id)
        media.license = {
            'label': {'en': 'Creative Commons Attribution Non-Commercial 4.0'},
            'source': self.second_portfolio_license,
        }
        media.save()

        # update archive
        response = client.put(
            f'/api/v1/archive?entry={entry_id}',
        )
        if response.status_code != 200:
            raise RuntimeError(f'testserver responded with code {response.status_code} and content {response.json()}')

        # byby ;-)
        client.logout()
        # store data for tests
        self.entry_id = entry_id
        self.archive_id = archive_id
        self.media_id = media_id

    def test_update_reflected_in_phaidra(self):
        media = Media.objects.get(pk=self.media_id)
        response = requests.get(f'https://services.phaidra-sandbox.univie.ac.at/api/object/{media.archive_id}/jsonld')
        phaidra_licenses = response.json()['edm:rights']
        self.assertEqual(
            phaidra_licenses,
            [
                self.second_phaidra_license,
            ],
        )


class EntryWithDeletedAttachmentUpdated(APITestCase):
    """> Portfolio–Phaidra: "Update Archive" fails, if previously archived
    asset has been deleted https://basedev.uni-ak.ac.at/redmine/issues/1654."""

    entry: Entry

    def setUp(self) -> None:
        """(Log in as a user)

        Create an entry, and media
        Archive them with the web api
        Delete media,
        Change entry,
        Update archive with the web api
        :return:
        """
        model_provider = ModelProvider()
        client_provider = ClientProvider(model_provider)
        # Tests will use the frameworks client
        self.client.login(username=model_provider.username, password=model_provider.peeword)

        # define title states for testing
        self.title_1 = 'Title 1'
        self.title_2 = 'Title 2'

        # Logic
        entry = model_provider.get_entry()
        entry.title = self.title_1
        entry.save()
        entry.refresh_from_db()

        media = model_provider.get_media(entry)
        archival_response = client_provider.get_media_primary_key_response(media, False)
        if archival_response.status_code != 200:
            raise RuntimeError(
                rf'Can not perform test {self.__class__}. '
                + rf'Server responded with status {archival_response.status_code} '
                + rf'and message {archival_response.content}'
            )

        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done
        entry.refresh_from_db()
        media.refresh_from_db()
        media.delete(keep_parents=True)

        entry.title = self.title_2
        entry.save()
        entry.refresh_from_db()

        # Pass data to tests
        self.entry = entry

    def test_update_is_working(self):
        # update archive
        portfolio_response = self.client.put(
            f'/api/v1/archive?entry={self.entry.id}',
        )
        self.assertEqual(
            portfolio_response.status_code,
            200,
            rf'Archival update for archived entry with deleted media returned message {portfolio_response.content}',
        )

        phaidra_response = requests.get(
            rf'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.entry.archive_id}/jsonld'
        )
        phaidra_data = phaidra_response.json()
        phaidra_title = phaidra_data['dce:title'][0]['bf:mainTitle'][0]['@value']
        self.assertEqual(phaidra_title, self.title_2)
