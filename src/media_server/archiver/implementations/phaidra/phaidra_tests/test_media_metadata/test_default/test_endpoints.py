from typing import TYPE_CHECKING, Optional

from rest_framework.test import APITestCase

from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Entry
from media_server.archiver.implementations.phaidra.phaidra_tests.test_media_metadata.test_thesis.utillities import (
    ClientProvider,
    ModelProvider,
)
from media_server.models import Media

if TYPE_CHECKING:
    from rest_framework.response import Response

from media_server.archiver import messages


class DefaultValidationEndpointTestCase(APITestCase):
    """Default aka not thesis."""

    entry: Optional['Entry'] = None
    media: Optional['Media'] = None

    def setUp(self) -> None:
        self.model_provider = ModelProvider()
        self.client_provider = ClientProvider(self.model_provider)

    def _create_media(self, title: bool = True, type_: bool = True, mime_type: bool = True, language=True) -> 'Media':
        self.entry = self.model_provider.get_entry(title=title, type_=type_, german_language=language)
        self.media = self.model_provider.get_media(entry=self.entry, mime_type=mime_type)
        self.media.file = SimpleUploadedFile('example.txt', b'example text')
        self.media.save()
        return self.media

    def get_media_primary_key_response(
        self, title: bool = True, type_: bool = True, mime_type: bool = True
    ) -> 'Response':
        self.media = self._create_media(title, type_, mime_type)
        return self.client_provider.get_media_primary_key_response(media=self.media, only_validate=True)

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
