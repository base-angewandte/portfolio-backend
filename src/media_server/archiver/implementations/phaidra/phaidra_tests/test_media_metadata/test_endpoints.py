from typing import TYPE_CHECKING

from rest_framework.test import APIClient, APITestCase

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Entry
from media_server.models import Media

if TYPE_CHECKING:
    from rest_framework.response import Response


class DefaultValidationEndpointTestCase(APITestCase):
    """Default aka not thesis."""

    def setUp(self) -> None:
        self.username = 'test-user'
        self.peeword = 'peeword'  # Yes, I am trying to trick some git hook …
        self.user = User.objects.create_user(username=self.username, password=self.peeword)
        self.client = APIClient()
        self.client.login(username=self.username, password=self.peeword)

    def _get_media(
        self, title: bool = True, type_: bool = True, license_: bool = True, mime_type: bool = True
    ) -> 'Media':
        entry = Entry(owner=self.user)
        if title:
            entry.title = 'A Title'
        if type_:
            entry.type = {
                'label': {'de': 'Installation', 'en': 'Installation'},
                'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/installation',
            }
        entry.save()
        media = Media(
            owner=self.user,
            file=SimpleUploadedFile('example.txt', b'example text'),
            entry_id=entry.id,
        )
        if mime_type:
            media.mime_type = 'text/plain'
        if license_:
            media.license = {
                'label': {'en': 'Creative Commons Attribution 4.0'},
                'source': 'http://base.uni-ak.ac.at/portfolio/licenses/CC-BY-4.0',
            }
        media.save()
        return media

    def get_media_primary_key_response(
        self, title: bool = True, type_: bool = True, license_: bool = True, mime_type: bool = True
    ) -> 'Response':
        media = self._get_media(title, type_, license_, mime_type)
        return self.client.get(
            f'/api/v1/validate_assets/media/{media.id}/',
        )

    def tearDown(self) -> None:
        self.client.logout()  # Very important! ;-)

    def test_missing_nothing(self):
        response = self.get_media_primary_key_response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Asset validation successful')

    def test_missing_title(self):
        """because title is default '' validation will succeed.

        :return:
        """
        response = self.get_media_primary_key_response(title=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Asset validation successful')

    def test_missing_type(self):
        response = self.get_media_primary_key_response(type_=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'type': [
                    'Missing data for required field.',
                ]
            },
        )

    def test_missing_mime_type(self):
        response = self.get_media_primary_key_response(mime_type=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'media': {
                    'mime_type': [
                        'Missing data for required field.',
                    ]
                }
            },
        )

    def test_missing_license(self):
        response = self.get_media_primary_key_response(license_=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'media': {
                    'license': [
                        'Missing data for required field.',
                    ]
                }
            },
        )

    def test_missing_every_mandatory_field(self):
        response = self.get_media_primary_key_response(
            title=False,
            type_=False,
            mime_type=False,
            license_=False,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                # no title!
                'type': [
                    'Missing data for required field.',
                ],
                'media': {
                    'mime_type': [
                        'Missing data for required field.',
                    ],
                    'license': [
                        'Missing data for required field.',
                    ],
                },
            },
        )


class WrongUserTestCase(APITestCase):
    pass  # todo


class NotAuthenticatedTestCase(APITestCase):
    pass  # todo
