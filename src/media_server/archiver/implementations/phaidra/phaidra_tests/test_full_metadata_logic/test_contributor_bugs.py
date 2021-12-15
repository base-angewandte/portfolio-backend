"""
A couple of different bugs / missing features concerning contributor translation and validation.

"""
import requests as requests
from django.test import TestCase
from rest_framework.test import APITestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import PhaidraThesisMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import \
    create_dynamic_phaidra_thesis_meta_data_schema
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import FakeBidirectionalConceptsMapper, \
    ModelProvider, ClientProvider


class Bug1659TranslationTestCase(TestCase):
    """
    https://basedev.uni-ak.ac.at/redmine/issues/1659

    A "free text" contributor should be present in the translated data.

    > Steps to reproduce:

    > * Create "Bachelor Thesis" entry, add an asset and fill out all required fields.
    > * Add an additional free text name as author.
    > * Archive

    """

    entry: 'Entry'
    translator: 'PhaidraThesisMetaDataTranslator'

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(thesis_type=True, author=False)
        cls.entry.data['authors'] = [
            {
                'label': 'Willy',
                'roles': [
                    {
                        'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/author',
                        'label': {'de': 'Autor*in', 'en': 'Author'}
                    }
                ]
            }
        ]
        cls.entry.save()
        cls.entry.refresh_from_db()
        # noinspection PyTypeChecker
        cls.translator = PhaidraThesisMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(cls.entry))
        cls.translated_data = cls.translator.translate_data(cls.entry)

    def test_free_contributor_in_translation(self):
        self.assertIn(
            'role:aut',
            self.translated_data['metadata']['json-ld']
        )
        self.assertEqual(
            len(self.translated_data['metadata']['json-ld']['role:aut']),
            1
        )


class Bug1659ValidationTestCase(TestCase):
    """
    https://basedev.uni-ak.ac.at/redmine/issues/1659

    A "free text" contributor should be present in the translated data.

    > Steps to reproduce:

    > * Create "Bachelor Thesis" entry, add an asset and fill out all required fields.
    > * Add an additional free text name as author.
    > * Archive

    """

    entry: 'Entry'

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(thesis_type=True, author=False)
        cls.entry.data['authors'] = [
            {
                'label': 'Willy',
                'roles': [
                    {
                        'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/author',
                        'label': {'de': 'Autor*in', 'en': 'Author'}
                    }
                ]
            }
        ]
        cls.entry.save()
        cls.entry.refresh_from_db()
        mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        # noinspection PyTypeChecker
        translator = PhaidraThesisMetaDataTranslator(mapping)
        cls.translated_data = translator.translate_data(cls.entry)
        # noinspection PyTypeChecker
        cls.schema = create_dynamic_phaidra_thesis_meta_data_schema(mapping)

    def test_free_contributor_validation(self):
        self.assertEqual(
            {},
            self.schema.validate(self.translated_data)
        )


class Bug1659FullIntegrationTestCase(APITestCase):

    entry: 'Entry'
    data: dict

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(thesis_type=True, author=False)
        cls.entry.data['authors'] = [
            {
                'label': 'Willy',
                'roles': [
                    {
                        'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/author',
                        'label': {'de': 'Autor*in', 'en': 'Author'}
                    }
                ]
            }
        ]
        cls.entry.save()
        cls.entry.refresh_from_db()

        media = model_provider.get_media(cls.entry)
        client_provider = ClientProvider(model_provider)
        response = client_provider.get_media_primary_key_response(media, only_validate=False)
        if response.status_code != 200:
            raise RuntimeError(f'Can not run test. Media archival failed with status code {response.status_code} '
                               f'and content {response.content}')
        cls.entry.refresh_from_db()
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{cls.entry.archive_id}/metadata',
        )
        if response.status_code != 200:
            raise RuntimeError(
                f'Can not run test. Retrieving entry\'s archive data from phaidra failed with status code '
                f'{response.status_code} and content {response.content}')
        cls.data = response.json()

    def test_phaidra_has_free_willy_author(self):
        self.assertIn(
            'role:aut',
            self.data['metadata']['JSON-LD']
        )
        authors = self.data['metadata']['JSON-LD']['role:aut']
        self.assertEqual(
            len(authors),
            1
        )
        author = authors[0]
        self.assertEqual(
            [],     # He's free
            author['skos:exactMatch']
        )
        self.assertEqual(
            'Willy',  # He's Willy
            author['schema:name'][0]['@value']
        )






