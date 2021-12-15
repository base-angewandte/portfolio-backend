"""
A couple of different bugs / missing features concerning contributor translation and validation.

"""
import requests as requests
from django.test import TestCase
from rest_framework.test import APITestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import \
    PhaidraThesisMetaDataTranslator
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


class Bug1671TestCase(TestCase):
    """
    https://basedev.uni-ak.ac.at/redmine/issues/1671

    Contributors with no role do not get committed to phaidra

    They should get the default role role:ctb
    """

    translated_data: dict
    validation: dict

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        entry = model_provider.get_entry(thesis_type=True, supervisor=True)
        entry.data['contributors'].append(
                {
                    'label': 'Willy',
                    'roles': []
                }
        )
        entry.save()
        entry.refresh_from_db()
        mapping = FakeBidirectionalConceptsMapper.from_entry(entry)
        # noinspection PyTypeChecker
        translator = PhaidraThesisMetaDataTranslator(mapping)
        cls.translated_data = translator.translate_data(entry)
        # noinspection PyTypeChecker
        schema = create_dynamic_phaidra_thesis_meta_data_schema(mapping)
        cls.validation = schema.validate(cls.translated_data)

    def test_free_willy_in_translated_data(self):
        self.assertIn(
            'role:ctb',
            self.translated_data['metadata']['json-ld']
        )
        ctbs = self.translated_data['metadata']['json-ld']['role:ctb']
        self.assertEqual(
            len(ctbs),
            1
        )
        ctb = ctbs[0]
        self.assertEqual(
            [],  # He's free
            ctb['skos:exactMatch']
        )
        self.assertEqual(
            'Willy',  # He's Willy
            ctb['schema:name'][0]['@value']
        )

    def test_free_role_less_is_ok(self):
        self.assertEqual(
            {},
            self.validation
        )


class Bug1672TestCase(TestCase):
    """
    https://basedev.uni-ak.ac.at/redmine/issues/1672

    Contributors get source of role assigned to phaidra

    Thy should get the source of the contributor
    """

    role_source = 'http://voc.uni-ak.ac.at/skosmos/povoc/en/page/another-role'
    contributor_source = 'http://d-nb.info/gnd/5299671-2'
    translated_data: dict

    @classmethod
    def setUpTestData(cls):
        entry = Entry(
            title='AnyContributor',
            data={
                'contributors': [
                    {
                        'label': 'Universität für Angewandte Kunst Wien',
                        'source': cls.contributor_source,
                        'roles': [
                            {
                                'source': cls.role_source,
                                'label': {'en': 'Actor', 'de': 'Darsteller*in'}
                            }
                        ]
                    }
                ]
            }
        )
        # noinspection PyTypeChecker
        cls.translated_data = PhaidraMetaDataTranslator(
            FakeBidirectionalConceptsMapper.from_entry(entry)
        ).translate_data(entry)['metadata']['json-ld']

    def test_right_source_chosen(self):
        self.assertIn(
            'role:csl',
            self.translated_data,
            'Key for fake role has not been generated'
        )
        csls = self.translated_data['role:csl']
        self.assertEqual(
            len(csls),
            1,
            'To many persons for fake role have been generated'
        )
        csl = csls[0]
        self.assertEqual(
            len(csl['skos:exactMatch']),
            1,
            'More then one match was generated'
        )
        match = csl['skos:exactMatch'][0]
        self.assertEqual(
            match['@value'],
            self.contributor_source
        )
