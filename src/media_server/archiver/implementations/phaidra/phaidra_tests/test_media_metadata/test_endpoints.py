from typing import TYPE_CHECKING

from rest_framework.test import APIClient, APITestCase

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Entry
from media_server.models import Media

if TYPE_CHECKING:
    from django.core.handlers.wsgi import WSGIRequest


class DefaultValidationEndpointTestCase(APITestCase):
    """Default aka not thesis."""

    def setUp(self) -> None:
        self.username = 'test-user'
        self.peeword = 'peeword'  # Yes, I am trying to trick some git hook …
        self.user = User.objects.create_user(username=self.username, password=self.peeword)
        self.client = APIClient()
        self.client.login(username=self.username, password=self.peeword)

    def _get_media(self, title: bool = True, type_: bool = True) -> 'Media':
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
        media.save()
        return media

    def get_media_primary_key_response(self, title: bool = True, type_: bool = True) -> 'WSGIRequest':
        media = self._get_media(title, type_)
        return self.client.get(
            f'/api/v1/validate_assets/media/{media.id}/',
        )

    def tearDown(self) -> None:
        self.client.logout()  # Very important! ;-)

    def test_missing_title(self):
        response = self.get_media_primary_key_response(title=False)
        print(response)
        self.assertIs(1, 2)

    def test_missing_type(self):
        raise NotImplementedError()

    def test_missing_type_and_title(self):
        raise NotImplementedError()

    def test_missing_nothing(self):
        raise NotImplementedError()


class WrongUserTestCase(APITestCase):
    pass  # todo


class NotAuthenticatedTestCase(APITestCase):
    pass  # todo
