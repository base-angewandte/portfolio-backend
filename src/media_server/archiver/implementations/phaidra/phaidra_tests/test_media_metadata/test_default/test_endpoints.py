from typing import TYPE_CHECKING, Optional

from rest_framework.test import APIClient, APITestCase

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Entry
from media_server.models import Media

if TYPE_CHECKING:
    from rest_framework.response import Response

from media_server.archiver import messages


class DefaultValidationEndpointTestCase(APITestCase):
    """Default aka not thesis."""

    entry: Optional['Entry'] = None
    media: Optional['Media'] = None

    def setUp(self) -> None:
        self.username = 'test-user'
        self.peeword = 'peeword'  # Yes, I am trying to trick some git hook …
        self.user = User.objects.create_user(username=self.username, password=self.peeword)
        self.client = APIClient()
        self.client.login(username=self.username, password=self.peeword)

    def _create_media(self, title: bool = True, type_: bool = True, mime_type: bool = True) -> 'Media':
        self.entry = Entry(owner=self.user)
        if title:
            self.entry.title = 'A Title'
        if type_:
            self.entry.type = {
                'label': {'de': 'Installation', 'en': 'Installation'},
                'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/installation',
            }
        self.entry.save()
        self.media = Media(
            owner=self.user,
            file=SimpleUploadedFile('example.txt', b'example text'),
            entry_id=self.entry.id,
        )
        if mime_type:
            self.media.mime_type = 'text/plain'

        self.media.license = {
            'label': {'en': 'Creative Commons Attribution 4.0'},
            'source': 'http://base.uni-ak.ac.at/portfolio/licenses/CC-BY-4.0',
        }

        self.media.save()
        return self.media

    def get_media_primary_key_response(
        self, title: bool = True, type_: bool = True, mime_type: bool = True
    ) -> 'Response':
        self.media = self._create_media(title, type_, mime_type)
        return self.client.get(
            f'/api/v1/validate_assets/media/{self.media.id}/',
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

    def test_missing_mime_type(self):
        response = self.get_media_primary_key_response(mime_type=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {'media': {'mime_type': [messages.validation.MISSING_DATA_FOR_REQUIRED_FIELD]}},
        )

    def test_missing_every_mandatory_field(self):
        response = self.get_media_primary_key_response(
            title=False,
            mime_type=False,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                # no title!
                'media': {
                    'mime_type': [messages.validation.MISSING_DATA_FOR_REQUIRED_FIELD],
                },
            },
        )


class WrongUserTestCase(APITestCase):
    pass  # todo


class NotAuthenticatedTestCase(APITestCase):
    pass  # todo
