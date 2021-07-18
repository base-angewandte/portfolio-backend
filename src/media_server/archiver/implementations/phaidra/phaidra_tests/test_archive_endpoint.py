from rest_framework.test import APITestCase

from media_server.archiver.implementations.phaidra.phaidra_tests.test_media_metadata.test_thesis.utillities import (
    ClientProvider,
    ModelProvider,
)


class ArchiveAssetTestcase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    def test_archive_asset(self):
        entry = self.model_provider.get_entry()
        asset = self.model_provider.get_media(entry)
        response = self.client_provider.get_media_primary_key_response(asset, only_validate=False)
        self.assertEqual(response.status_code, 200)

    def test_update_asset(self):
        pass
