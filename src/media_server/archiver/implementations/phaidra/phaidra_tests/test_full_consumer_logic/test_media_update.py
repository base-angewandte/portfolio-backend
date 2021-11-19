import json

from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import django_rq
import requests

from media_server.models import Media


class OnePdfResaved(APITestCase):

    def setUp(self) -> None:
        """
        (Log in as a user)

        Create an entry with the web api,
        attach a file with the web api,
        archive the file with the web api,
        change the media with the web api,
        update archive with the web api
        :return:
        """
        User.objects.create_user(username='Hansi', password='Hansi1986')
        client = self.client
        client.login(username='Hansi', password='Hansi1986')

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
                'license': json.dumps({
                    'source': self.first_portfolio_license,
                    'label': {'de': 'urheberrechtlich geschützt', "en": "Copyright"}
                }),
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
                            'label': {'en': "Creative Commons Attribution Non-Commercial 4.0"},
                            "source": self.second_portfolio_license,
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
            [self.second_phaidra_license, ]
        )
