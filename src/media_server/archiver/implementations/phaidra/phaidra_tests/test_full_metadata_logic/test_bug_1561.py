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
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import \
    PhaidraThesisMetaDataTranslator
from media_server.archiver.implementations.phaidra.metadata.thesis.must_use import DEFAULT_DYNAMIC_ROLES
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import \
    create_dynamic_phaidra_thesis_meta_data_schema
from media_server.archiver.messages.validation.thesis import MISSING_SUPERVISOR

if typing.TYPE_CHECKING:
    from core.models import Entry
    from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import \
        PhaidraThesisContainer, PhaidraThesisMetaData

# Utilities
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider, \
    FakeBidirectionalConceptsMapper, PhaidraContainerGenerator, add_other_role, add_other_phaidra_role


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
    schema: 'PhaidraThesisMetaData'
    inner_schema: 'PhaidraThesisContainer'
    phaidra_errors: dict

    entry_kwargs = {'supervisor': False, 'thesis_type': True}
    phaidra_container_kwargs = {'respect_supervisor_role': False}
    translator_class: typing.Type[PhaidraThesisMetaDataTranslator] = PhaidraThesisMetaDataTranslator

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DEFAULT_DYNAMIC_ROLES)
        # noinspection PyTypeChecker
        cls.schema = create_dynamic_phaidra_thesis_meta_data_schema(cls.mapping)
        # to not have to this in every test
        cls.inner_schema = cls.schema.fields['metadata'].nested.fields['json_ld'].nested
        cls.phaidra_errors = cls.schema.validate(
            PhaidraContainerGenerator().create_phaidra_container(**cls.phaidra_container_kwargs)
        )

    def test_no_role_supervisor_in_generated_data(self):
        # noinspection PyTypeChecker
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']
        )

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """The field is required in the schema"""
        # noinspection PyTypeChecker
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']
        )

    def test_correct_translated_supervisor_value_in_generated_data(self):
        """No supervisor -> empty data"""
        # noinspection PyTypeChecker
        self.assertEqual(
            [],
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']['role:dgs']
        )

    def test_schema_has_no_supervisor_field(self):
        """The schema should not have NOT translated supervisor field"""
        self.assertNotIn(
            'role_supervisor',
            self.inner_schema.fields
        )

    def test_schema_has_translated_supervisor_field(self):
        """The schema should have the dynamically translated supervisor field"""
        self.assertIn(
            'role_dgs',
            self.inner_schema.fields
        )

    def test_custom_validation_mechanism_added_in_schema(self):
        """The field should differ from other dynamic fields: required=True, validator=MissingSupervisorValidator"""
        self.assertEqual(len(self.inner_schema.custom_validation_callables), 1)
        self.assertEqual(self.inner_schema.custom_validation_callables[0].key, 'role:dgs')

    def test_schema_validation(self):
        """A schema should return a validation error for missing supervisor"""
        self.assertEqual(
            self.phaidra_errors,
            {
                'metadata': {
                    'json-ld': {
                        'role:dgs': [MISSING_SUPERVISOR, ]
                    }
                }
            }
        )


class ThesisWithSupervisorTestCase(ThesisNoRolesTestCase):
    entry_kwargs = {'supervisor': True, 'thesis_type': True}
    phaidra_container_kwargs = {
        'respect_supervisor_role': True,
        # by adding another error, we can specifically look up the supervisor error, instead of comparing to {}/no error
        'respect_german_abstract_rule': False,
    }

    def test_correct_translated_supervisor_value_in_generated_data(self):
        """A supervisor must be translated"""
        expected = [
                {
                    '@type': 'schema:Person',
                    'skos:exactMatch': [
                        {
                            '@value': 'http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor',
                            '@type': 'ids:uri'
                        },
                    ],
                    'schema:name': [
                        {
                            '@value': 'Universität für Angewandte Kunst Wien',
                        },
                    ]
                }
            ]
        # noinspection PyTypeChecker
        generated = self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']['role:dgs']
        self.assertEqual(expected, generated)

    def test_schema_validation(self):
        """A schema should not return a validation error for existing supervisor"""
        self.assertNotIn(
            'role:dgs',
            self.phaidra_errors['metadata']['json-ld']
        )


class ThesisWithSupervisorAndOtherRoleTestCase(ThesisNoRolesTestCase):
    entry_kwargs = {'supervisor': True, 'thesis_type': True}
    phaidra_container_kwargs = {
        'respect_supervisor_role': True,
        'respect_english_abstract_rule': False,
        # Provoke validation error, to explicitly for supervisor key
    }

    @classmethod
    def setUpTestData(cls):
        """I know, it's not DRY, but it is just a test … ?"""
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(**cls.entry_kwargs)
        cls.translator = cls.translator_class()
        cls.entry = add_other_role(cls.entry)
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DEFAULT_DYNAMIC_ROLES)
        # noinspection PyTypeChecker
        cls.schema = create_dynamic_phaidra_thesis_meta_data_schema(cls.mapping)
        # to not have to this in every test
        cls.inner_schema = cls.schema.fields['metadata'].nested.fields['json_ld'].nested
        phaidra_container = PhaidraContainerGenerator().create_phaidra_container(**cls.phaidra_container_kwargs)
        phaidra_container = add_other_phaidra_role(phaidra_container)
        cls.phaidra_errors = cls.schema.validate(phaidra_container)

    def test_correct_translated_supervisor_value_in_generated_data(self):
        """A supervisor must be translated"""
        expected = [
                {
                    '@type': 'schema:Person',
                    'skos:exactMatch': [
                        {
                            '@value': 'http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor',
                            '@type': 'ids:uri'
                        },
                    ],
                    'schema:name': [
                        {
                            '@value': 'Universität für Angewandte Kunst Wien',
                        },
                    ]
                }
            ]
        # noinspection PyTypeChecker
        generated = self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']['role:dgs']
        self.assertEqual(expected, generated)

    def test_schema_validation(self):
        """A schema should not return a validation error for existing supervisor"""
        self.assertNotIn(
            'role:dgs',
            self.phaidra_errors['metadata']['json-ld']
        )


class ThesisWithNoSupervisorButOtherRoleTestCase(ThesisWithSupervisorAndOtherRoleTestCase):
    """
    Next TestCase will be called SupercalifragilisticexpialidociousTestCase. Hey, that has the same length *sigh*
    """
    entry_kwargs = {'supervisor': False, 'thesis_type': True}
    phaidra_container_kwargs = {
        'respect_supervisor_role': False,
    }

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """The field is required in the schema"""
        # noinspection PyTypeChecker
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']
        )

    def test_correct_translated_supervisor_value_in_generated_data(self):
        """No supervisor -> empty data"""
        # noinspection PyTypeChecker
        self.assertEqual(
            [],
            self.translator.translate_data(self.entry, self.mapping)['metadata']['json-ld']['role:dgs']
        )

    def test_schema_validation(self):
        inner_errors = self.phaidra_errors['metadata']['json-ld']
        self.assertIn('role:dgs', inner_errors)
        self.assertEqual(
            inner_errors['role:dgs'],
            [MISSING_SUPERVISOR, ]
        )
