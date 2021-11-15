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
from dataclasses import dataclass, field

from rest_framework.test import APITestCase

from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import \
    PhaidraThesisMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.thesis.must_use import DYNAMIC_ROLES

if typing.TYPE_CHECKING:
    from core.models import Entry


# Utilities
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider


@dataclass
class FakeConceptMapper:
    """Fake-Map an concept (uri) to others from skosmos."""

    '''Base uri, eg https://voc.uni-ak.ac.at/skosmos/povoc/en/page/advisor'''
    uri: str

    '''comparables, eg  {'http://vocab.getty.edu/aat/300160216', 'http://d-nb.info/gnd/4005565-6'}'''
    owl_sameAs: typing.Set[str]

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

    def to_dict(self) -> dict:
        return {
            'uri': self.uri,
            'owl:sameAs': self.owl_sameAs,
        }


@dataclass
class FakeBidirectionalConceptsMapper:
    concept_mappings: typing.Dict[str, FakeConceptMapper] = field(default_factory=dict)

    @classmethod
    def from_base_uris(cls, uris: typing.Set[str]) -> 'FakeBidirectionalConceptsMapper':
        return cls(concept_mappings={uri: FakeConceptMapper.from_base_uri(uri) for uri in uris})

    def get_owl_sameAs_from_uri(self, uri: str) -> typing.Set[str]:
        return self.concept_mappings[uri].owl_sameAs

    def get_uris_from_owl_sameAs(self, owl_sameAs: str) -> typing.Set[str]:
        return {
            uri for uri, concept_mapper in self.concept_mappings.items() if owl_sameAs in concept_mapper.owl_sameAs
        }

    def add_uri(self, uri: str) -> 'FakeBidirectionalConceptsMapper':
        if uri not in self.concept_mappings:
            self.concept_mappings[uri] = FakeConceptMapper.from_base_uri(uri)
        return self

    def add_uris(self, uris: typing.Set[str]) -> 'FakeBidirectionalConceptsMapper':
        for uri in uris:
            self.add_uri(uri)
        return self

    @classmethod
    def from_entry(cls, entry: 'Entry') -> 'FakeBidirectionalConceptsMapper':
        if (entry.data is None) or ('contributors' not in entry.data):
            return cls.from_base_uris(set())
        contributors = entry.data['contributors']
        roles = []
        for contributor in contributors:
            if 'roles' in contributor:
                for role in contributor['roles']:
                    if 'source' in role:
                        roles.append(role['source'])
        return cls.from_base_uris(set(roles))


def add_other_role(entry: 'Entry') -> 'Entry':
    if 'contributors' not in entry.data:
        entry.data['contributors'] = []

    entry.data['contributors'].append(
        {
            'label': 'Universität für Angewandte Kunst Wien',
            'roles': [
                {
                    'label': {'de': 'Supervisor', 'en': 'supervisor'},
                    'source': 'http://voc.uni-ak.ac.at/skosmos/povoc/en/page/another-role',
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

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """Since this is no thesis, this role is not required"""
        self.assertNotIn(
            'role:dgs',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )


class NoThesisSupervisorTestCase(NoThesisNoRolesTestCase):
    entry_kwargs = {'supervisor': True, 'thesis_type': False}

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """No dynamic translation here"""
        self.assertNotIn(
            'role:dgs',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )


class ThesisNoRolesTestCase(NoThesisNoRolesTestCase):
    mapping: FakeBidirectionalConceptsMapper
    translator: PhaidraThesisMetaDataTranslator

    entry_kwargs = {'supervisor': False, 'thesis_type': True}
    translator_class: typing.Type[PhaidraThesisMetaDataTranslator] = PhaidraThesisMetaDataTranslator

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DYNAMIC_ROLES)

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']
        )

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """The field is required in the schema"""
        self.assertIn(
            'role:dgs',
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
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DYNAMIC_ROLES)


class ThesisWithNoSupervisorButOtherRoleTestCase(ThesisWithSupervisorAndOtherRoleTestCase):
    """
    Next TestCase will be called SupercalifragilisticexpialidociousTestCase. Hey, that has the same length *sigh*
    """
    entry_kwargs = {'supervisor': False, 'thesis_type': True}

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """The field is required in the schema"""
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']
        )
