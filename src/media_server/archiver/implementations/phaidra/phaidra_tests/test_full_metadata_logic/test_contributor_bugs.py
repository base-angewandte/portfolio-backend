"""
A couple of different bugs / missing features concerning contributor translation and validation.

"""
from django.test import TestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import FakeBidirectionalConceptsMapper, \
    ModelProvider


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
    translator: 'PhaidraMetaDataTranslator'

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
        cls.translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(cls.entry))
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


