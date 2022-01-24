from rest_framework.test import APITestCase

from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ClientProvider, ModelProvider

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.models import Entry


class ArchiveAssetTestcase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)
        cls.entry = cls.model_provider.get_entry()
        cls.asset = cls.model_provider.get_media(cls.entry)

    def test_archive_asset(self):
        response = self.client_provider.get_media_primary_key_response(self.asset, only_validate=False)
        self.assertEqual(response.status_code, 200)

    def test_update_asset(self):
        self.entry.title = 'New Title'
        response = self.client_provider.get_media_primary_key_response(self.asset, only_validate=False)
        self.assertEqual(response.status_code, 200)


class ArchiveAssetWithEntryWithNoType(APITestCase):
    """
            Roman:
    > If you attempt to archive the attachment from an entry that has no type,
    > the validate_assets API returns status code
    > 500 and the response body is like:
    > `InternalValidationError at /api/v1/validate_assets/media/u6zg7SUvwrQyes4u7QUPw9/`
    > `['Language is required']`
    """

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)
        cls.entry = cls.model_provider.get_entry(
            title=True,
            type_=False,
            thesis_type=False,
            german_language=False,
            akan_language=False,
            author=False,
            supervisor=False,
            english_abstract=False,
            german_abstract=False,
            french_abstract=False,
        )
        cls.asset = cls.model_provider.get_media(cls.entry)

    def test_successful_validation(self):
        response = self.client_provider.get_media_primary_key_response(self.asset, only_validate=True)
        self.assertEqual(response.status_code, 200)


class ArchiveSecondAsset(APITestCase):
    """> If an entry has already been archived successfully (e.g. "View in
    Phaidra" button is shown at the top),

        > attempting to push to archive a second attachment from the same entry results in the following response from
        > the archive_assets API:
    ```RuntimeError at /api/v1/archive_assets/media/65iBsTkazHjuoETmb9ayLV/
    Phaidra returned with response <Response [404]> and content b'Not found\n'```
    """

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)
        cls.entry = cls.model_provider.get_entry(
            title=True,
            type_=False,
            thesis_type=False,
            german_language=False,
            akan_language=False,
            author=False,
            supervisor=False,
            english_abstract=False,
            german_abstract=False,
            french_abstract=False,
        )
        cls.asset_1 = cls.model_provider.get_media(cls.entry)
        cls.response = cls.client_provider.get_media_primary_key_response(cls.asset_1, only_validate=False)
        cls.asset_2 = cls.model_provider.get_media(cls.entry)

    def test_archive_secondary_asset(self):
        response = self.client_provider.get_media_primary_key_response(self.asset_2, only_validate=False)
        self.assertEqual(response.status_code, 200)


class ValidateValidEntryEndpoint(APITestCase):
    """
    With no attachment
    https://basedev.uni-ak.ac.at/redmine/issues/1711
    """
    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.client_provider = ClientProvider(model_provider)
        cls.entry = model_provider.get_entry()

    def test_validation(self):
        response = self.client_provider.get_validate_entry_response(self.entry)
        self.assertEqual(response.status_code, 200, rf'Response {response} with {response.content}')


class ValidateInvalidEntryEndpoint(APITestCase):
    """
    With no attachment
    https://basedev.uni-ak.ac.at/redmine/issues/1711
    """

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.client_provider = ClientProvider(model_provider)
        cls.entry = model_provider.get_entry(english_abstract=False)

    def test_validation(self):
        response = self.client_provider.get_validate_entry_response(self.entry)
        self.assertEqual(response.status_code, 400, rf'Response {response} with {response.content}')
        self.assertIn('texts', response.data, rf'texts not found in {response.data}')


class ValidateValidEntryWithAttachmentsEndpoint(APITestCase):
    """
    With attachment
    https://basedev.uni-ak.ac.at/redmine/issues/1711
    """

    entry: 'Entry'

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.client_provider = ClientProvider(model_provider)
        cls.entry = model_provider.get_entry()
        media = model_provider.get_media(entry=cls.entry)

    def test_validation(self):
        response = self.client_provider.get_validate_entry_response(self.entry)
        self.assertEqual(response.status_code, 200, rf'Response {response} with {response.content}')


class ValidateInvalidEntryWithAttachmentsEndpoint(APITestCase):
    """
    With attachment
    https://basedev.uni-ak.ac.at/redmine/issues/1711
    """
    entry: 'Entry'

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.client_provider = ClientProvider(model_provider)
        cls.entry = model_provider.get_entry(english_abstract=False)
        media = model_provider.get_media(entry=cls.entry)

    def test_validation(self):
        response = self.client_provider.get_validate_entry_response(self.entry)
        self.assertEqual(response.status_code, 400, rf'Response is {response.content}')
        self.assertIn('texts', response.data, rf'texts not found in {response.data}')
