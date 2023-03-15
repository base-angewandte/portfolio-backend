"""# Portfolio–Phaidra BE: Contributors are missing in Phaidra for certain
types

https://basedev.uni-ak.ac.at/redmine/issues/1656

> Christoph Hoffmann: "was able to reproduce, this seems to be the case for all contributors submitted through types
> that do not pass the thesis validation"
"""
import requests
from rest_framework.test import APITestCase

from django.test import TestCase

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import (
    ClientProvider,
    FakeBidirectionalConceptsMapper,
    ModelProvider,
)


class NotThesisContributorsTestCase(APITestCase):
    """Reproduce from the Web-API-Consumer-View."""

    phaidra_data: dict

    @classmethod
    def setUpTestData(cls):
        """Steps to reproduce:

        Create entry with type "Article" Add contributors with roles Add
        and archive an asset
        """
        model_provider = ModelProvider()
        client_provider = ClientProvider(model_provider)
        # The supervisor is a part of the contributors
        entry = model_provider.get_entry(thesis_type=False, supervisor=True)
        media = model_provider.get_media(entry)
        response = client_provider.get_media_primary_key_response(media, only_validate=False)
        if response.status_code != 200:
            raise RuntimeError(
                f'Can not perform test. Media Archival returned status code {response.status_code}'
                f' with message {response.content}'
            )
        entry.refresh_from_db()
        url = f'https://services.phaidra-sandbox.univie.ac.at/api/object/{entry.archive_id}/jsonld'
        response = requests.get(url)
        if response.status_code != 200:
            raise RuntimeError(
                f'Phaidra response <{url}> status not 200, but {response.status_code} with message {response.text}'
            )
        cls.phaidra_data = response.json()

    def test_contributors_should_appear_in_phaidra(self):
        self.assertIn('role:dgs', self.phaidra_data)


class NotThesisWithContributorDataTranslationTestCase(TestCase):
    """Check if the data is generated on our site."""

    translated_data: dict

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        # The supervisor is a part of the contributors
        entry = model_provider.get_entry(thesis_type=False, supervisor=True)
        # noinspection PyTypeChecker
        translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(entry))
        cls.translated_data = translator.translate_data(entry)

    def test_contributors_should_appear_in_data_for_phaidra(self):
        self.assertIn('role:dgs', self.translated_data['metadata']['json-ld'])
