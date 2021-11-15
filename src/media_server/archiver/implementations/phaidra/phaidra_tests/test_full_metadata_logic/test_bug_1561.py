"""
https://basedev.uni-ak.ac.at/redmine/issues/1561

After having a talk with Christoph Hoffmann, we came to the agreement, that the following is required:

- Removal of static role:supervisor
- Must use schema validation for the dynamic skosmos translation of role:supervisor

Along with the current implementation and some quirks of the old marshmallow library, this leads to the following
code requirements:

- Translator:
  -data translation:
    - do not return role:supervisor role
    - return role with :supervisor-translation
      - [] on no supervisor
      - [object, …] on supervisor-translation
  - error translation:
    # TODO: match previous result
    - translate {role:supervisor-translation: [Error-Codes] ro {role:supervisor: [Error-Codes]} 

- Schema:
    - on role:supervisor-translation = [] return   role:supervisor-translation: [MISSING_SUPERVISOR]
    # TODO: match previous result, just other property!

- Full consumer logic test
  - thesis no supervisor
  - thesis supervisor
  - thesis no supervisor, other roles
  - thesis supervisor, other roles
  - no thesis, no supervisor
  - thesis, supervisor

"""
import typing

from rest_framework.test import APITestCase

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import \
    BidirectionalConceptsMapper, ConceptMapper
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import \
    PhaidraThesisMetaDataTranslator

if typing.TYPE_CHECKING:
    from core.models import Entry


# Utilities
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider


class FakeConceptMapper(ConceptMapper):
    """Fake-Map an concept (uri) to others from skosmos."""

    class Utils:
        fakes = {
            'http://voc.uni-ak.ac.at/skosmos/povoc/en/page/another-role': {'http://id.loc.gov/vocabulary/relators/csl'},
            'http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor': {'http://id.loc.gov/vocabulary/relators/dgs'},
        }

    @classmethod
    def from_base_uri(cls, uri: str) -> 'FakeConceptMapper':
        return cls(
            uri=uri,
            owl_sameAs=cls.Utils.fakes[uri]
        )


ConceptMapper = FakeConceptMapper


def add_other_role(entry: 'Entry') -> 'Entry':
    if 'contributors' not in entry.data:
        entry.data['contributors'] = []

    entry.data['contributors'].append(
        {
            'label': 'Universität für Angewandte Kunst Wien',
            'roles': [
                {
                    'label': {'de': 'Supervisor', 'en': 'supervisor'},
                    'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor',
                }
            ],
        },
    )
    entry.save()
    entry.refresh_from_db()
    return entry


# Tests!


class NoThesisNoRolesTestCase(APITestCase):

    entry: 'Entry'
    translator: 'PhaidraMetaDataTranslator'

    entry_kwargs = {'supervisor': False, 'thesis_type': False}
    translator_class: typing.Type['PhaidraMetaDataTranslator'] = PhaidraMetaDataTranslator

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(**cls.entry_kwargs)
        cls.translator = cls.translator_class()

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )


class NoThesisSupervisorTestCase(NoThesisNoRolesTestCase):
    entry_kwargs = {'supervisor': True, 'thesis_type': False}


class ThesisNoRolesTestCase(NoThesisNoRolesTestCase):
    mapping: BidirectionalConceptsMapper
    translator: PhaidraThesisMetaDataTranslator

    entry_kwargs = {'supervisor': False, 'thesis_type': True}
    translator_class: typing.Type[PhaidraThesisMetaDataTranslator] = PhaidraThesisMetaDataTranslator

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mapping = BidirectionalConceptsMapper.from_entry(cls.entry)

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']
        )


class ThesisWithSupervisorTestCase(ThesisNoRolesTestCase):
    entry_kwargs = {'supervisor': True, 'thesis_type': True}


class ThesisWithSupervisorAndOtherRoleTestCase(ThesisNoRolesTestCase):
    entry_kwargs = {'supervisor': True, 'thesis_type': True}

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(**cls.entry_kwargs)
        cls.translator = cls.translator_class()
        cls.entry = add_other_role(cls.entry)
        cls.mapping = BidirectionalConceptsMapper.from_entry(cls.entry)


class ThesisWithNoSupervisorButOtherRoleTestCase(ThesisWithSupervisorAndOtherRoleTestCase):
    """
    Next TestCase will be called SupercalifragilisticexpialidociousTestCase. Hey, that has the same length *sigh*
    """
    entry_kwargs = {'supervisor': False, 'thesis_type': True}
