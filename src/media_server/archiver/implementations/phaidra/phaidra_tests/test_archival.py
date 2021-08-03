import requests
from rest_framework.test import APITestCase

from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ClientProvider, ModelProvider


class TestArchival(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)
        cls.entry = cls.model_provider.get_entry()
        cls.asset = cls.model_provider.get_media(cls.entry)

    def test_full_archival_logic(self):
        response = self.client_provider.get_media_primary_key_response(self.asset, only_validate=False)
        id_ = response.data['object']
        phaidra_data = self._get_info_from_phaidra(id_)
        self.assertIn('dcterms:language', phaidra_data)  # e. g.

    def _get_info_from_phaidra(self, id_: str) -> dict:
        return requests.get(f'https://services.phaidra-sandbox.univie.ac.at/api/object/{id_}/jsonld').json()
