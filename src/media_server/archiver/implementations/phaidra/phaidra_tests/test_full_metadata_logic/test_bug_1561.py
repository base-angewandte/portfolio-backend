"""
https://basedev.uni-ak.ac.at/redmine/issues/1561

This file contains two parts: One, that tests the issue itself and later on a part with a lot of test classes, that
check the steps to solve the issue.

Here is description, of what is to do:

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

import requests
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

from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider, ClientProvider, \
    FakeBidirectionalConceptsMapper, PhaidraContainerGenerator, add_other_role, add_other_phaidra_role


# --------------------------
# Issue TestCase
# --------------------------

class ArchivedSupervisorRole(APITestCase):

    entry_archive_id: str

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        entry = model_provider.get_entry(supervisor=True)
        media = model_provider.get_media(entry)
        client_provider = ClientProvider(model_provider)
        response = client_provider.get_media_primary_key_response(media, only_validate=False)
        if response.status_code != 200:
            raise RuntimeError(
                f'Failed to set up test data. Server responded with status code {response.status_code} '
                f'and content {response.content}'
            )
        entry.refresh_from_db()
        archive_id = entry.archive_id
        response = requests.get(f'https://services.phaidra-sandbox.univie.ac.at/api/object/{archive_id}/jsonld')
        if response.status_code != 200:
            raise RuntimeError(
                f'Failed to set up test data. Phaidra responded with status code {response.status_code} '
                f'and content {response.content}'
            )
        cls.phaidra_data = response.json()

    def test_no_role_supervisor_in_phaidra(self):
        self.assertNotIn(
            'role:supervisor',
            self.phaidra_data
        )

    def test_translated_supervisor_in_phaidra(self):
        self.assertIn(
            'role:dgs',
            self.phaidra_data
        )


# -------------------------------
# Steps to solve issue test cases
# -------------------------------


class NoThesisNoRolesTestCase(APITestCase):

    entry: 'Entry'
    translator: 'PhaidraMetaDataTranslator'

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(supervisor=False, thesis_type=False)
        # noinspection PyTypeChecker
        cls.translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(cls.entry))

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


class NoThesisSupervisorTestCase(APITestCase):

    entry: 'Entry'
    translator: 'PhaidraMetaDataTranslator'

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(supervisor=True, thesis_type=False)
        # noinspection PyTypeChecker
        cls.translator = PhaidraMetaDataTranslator(FakeBidirectionalConceptsMapper.from_entry(cls.entry))

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """Still dynamic translation here"""
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )


class ThesisNoRolesTestCase(APITestCase):
    entry: 'Entry'
    translator: 'PhaidraMetaDataTranslator'
    mapping: FakeBidirectionalConceptsMapper
    translator: PhaidraThesisMetaDataTranslator
    schema: 'PhaidraThesisMetaData'
    inner_schema: 'PhaidraThesisContainer'
    phaidra_errors: dict

    expected_phaidra_error = {
                'metadata': {
                    'json-ld': {
                        'role:dgs': [MISSING_SUPERVISOR, ]
                    }
                }
            }

    expected_portfolio_error = {
        'data': {
            'contributors': [MISSING_SUPERVISOR, ]
        }
    }

    @classmethod
    def setUpTestData(cls):
        mode_provider = ModelProvider()
        cls.entry = mode_provider.get_entry(supervisor=False, thesis_type=False)
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DEFAULT_DYNAMIC_ROLES)
        # noinspection PyTypeChecker
        cls.translator = PhaidraThesisMetaDataTranslator(cls.mapping)
        # noinspection PyTypeChecker
        cls.schema = create_dynamic_phaidra_thesis_meta_data_schema(cls.mapping)
        # to not have to this in every test
        cls.inner_schema = cls.schema.fields['metadata'].nested.fields['json_ld'].nested
        cls.phaidra_errors = cls.schema.validate(
            PhaidraContainerGenerator().create_phaidra_container(respect_supervisor_role=False)
        )

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """The field is required in the schema"""
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )

    def test_correct_translated_supervisor_value_in_generated_data(self):
        """No supervisor -> empty data"""
        self.assertEqual(
            [],
            self.translator.translate_data(self.entry)['metadata']['json-ld']['role:dgs']
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
            self.expected_phaidra_error,
        )

    def test_error_translation(self):
        """The phaidra error from marshmallow should be mapped to the portfolio scheme"""
        self.assertEqual(
            self.expected_portfolio_error,
            self.translator.translate_errors(self.expected_phaidra_error)
        )


class ThesisWithSupervisorTestCase(APITestCase):
    entry: 'Entry'
    translator: 'PhaidraMetaDataTranslator'
    mapping: FakeBidirectionalConceptsMapper
    translator: PhaidraThesisMetaDataTranslator
    schema: 'PhaidraThesisMetaData'
    inner_schema: 'PhaidraThesisContainer'
    phaidra_errors: dict

    @classmethod
    def setUpTestData(cls):
        mode_provider = ModelProvider()
        cls.entry = mode_provider.get_entry(supervisor=True, thesis_type=True)
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DEFAULT_DYNAMIC_ROLES)
        # noinspection PyTypeChecker
        cls.translator = PhaidraThesisMetaDataTranslator(cls.mapping)
        # noinspection PyTypeChecker
        cls.schema = create_dynamic_phaidra_thesis_meta_data_schema(cls.mapping)
        # to not have to this in every test
        cls.inner_schema = cls.schema.fields['metadata'].nested.fields['json_ld'].nested
        cls.phaidra_errors = cls.schema.validate(
            PhaidraContainerGenerator().create_phaidra_container(
                respect_supervisor_role=True, respect_german_abstract_rule=False
            )
        )

    def test_custom_validation_mechanism_added_in_schema(self):
        """The field should differ from other dynamic fields: required=True, validator=MissingSupervisorValidator"""
        self.assertEqual(len(self.inner_schema.custom_validation_callables), 1)
        self.assertEqual(self.inner_schema.custom_validation_callables[0].key, 'role:dgs')

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

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )

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
        generated = self.translator.translate_data(self.entry)['metadata']['json-ld']['role:dgs']
        self.assertEqual(expected, generated)

    def test_schema_validation(self):
        """A schema should not return a validation error for existing supervisor"""
        self.assertNotIn(
            'role:dgs',
            self.phaidra_errors['metadata']['json-ld']
        )

    def test_error_translation(self):
        """There should be no supervisor error in the translated errors (and therefore no parent property data)"""
        self.assertNotIn(
            'data',
            self.translator.translate_errors(self.phaidra_errors)
        )

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """Since this is a thesis, this role is required"""
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )


class ThesisWithSupervisorAndOtherRoleTestCase(APITestCase):
    entry: 'Entry'
    translator: 'PhaidraMetaDataTranslator'
    mapping: FakeBidirectionalConceptsMapper
    translator: PhaidraThesisMetaDataTranslator
    schema: 'PhaidraThesisMetaData'
    inner_schema: 'PhaidraThesisContainer'
    phaidra_errors: dict

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(supervisor=True, thesis_type=True)
        cls.entry = add_other_role(cls.entry)
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DEFAULT_DYNAMIC_ROLES)
        # noinspection PyTypeChecker
        cls.translator = PhaidraThesisMetaDataTranslator(cls.mapping)
        # noinspection PyTypeChecker
        cls.schema = create_dynamic_phaidra_thesis_meta_data_schema(cls.mapping)
        # to not have to this in every test
        cls.inner_schema = cls.schema.fields['metadata'].nested.fields['json_ld'].nested
        phaidra_container = PhaidraContainerGenerator().create_phaidra_container(
            respect_supervisor_role=True,
            respect_english_abstract_rule=False  # Provoke validation error
        )
        phaidra_container = add_other_phaidra_role(phaidra_container)
        cls.phaidra_errors = cls.schema.validate(phaidra_container)

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )

    def test_custom_validation_mechanism_added_in_schema(self):
        """The field should differ from other dynamic fields: required=True, validator=MissingSupervisorValidator"""
        self.assertEqual(len(self.inner_schema.custom_validation_callables), 1)
        self.assertEqual(self.inner_schema.custom_validation_callables[0].key, 'role:dgs')

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
        generated = self.translator.translate_data(self.entry)['metadata']['json-ld']['role:dgs']
        self.assertEqual(expected, generated)

    def test_schema_validation(self):
        """A schema should not return a validation error for existing supervisor"""
        self.assertNotIn(
            'role:dgs',
            self.phaidra_errors['metadata']['json-ld']
        )

    def test_error_translation(self):
        """There should be no supervisor in the translated error result (and therefore no parent property data)"""
        self.assertNotIn(
            'data',
            self.translator.translate_errors(self.phaidra_errors)
        )

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """Since this is a thesis, this role is required"""
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )


class ThesisWithNoSupervisorButOtherRoleTestCase(APITestCase):
    """
    Next TestCase will be called SupercalifragilisticexpialidociousTestCase. Hey, that has the same length *sigh*
    """

    entry: 'Entry'
    translator: 'PhaidraMetaDataTranslator'
    mapping: FakeBidirectionalConceptsMapper
    translator: PhaidraThesisMetaDataTranslator
    schema: 'PhaidraThesisMetaData'
    inner_schema: 'PhaidraThesisContainer'
    phaidra_errors: dict

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry(supervisor=False, thesis_type=True)
        cls.entry = add_other_role(cls.entry)
        cls.mapping = FakeBidirectionalConceptsMapper.from_entry(cls.entry)
        cls.mapping.add_uris(DEFAULT_DYNAMIC_ROLES)
        # noinspection PyTypeChecker
        cls.translator = PhaidraThesisMetaDataTranslator(cls.mapping)
        # noinspection PyTypeChecker
        cls.schema = create_dynamic_phaidra_thesis_meta_data_schema(cls.mapping)
        # to not have to this in every test
        cls.inner_schema = cls.schema.fields['metadata'].nested.fields['json_ld'].nested
        phaidra_container = PhaidraContainerGenerator().create_phaidra_container(
            respect_supervisor_role=False,
        )
        phaidra_container = add_other_phaidra_role(phaidra_container)
        cls.phaidra_errors = cls.schema.validate(phaidra_container)

    def test_correct_translated_supervisor_property_in_generated_data(self):
        """The field is required in the schema"""
        self.assertIn(
            'role:dgs',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )

    def test_no_role_supervisor_in_generated_data(self):
        self.assertNotIn(
            'role:supervisor',
            self.translator.translate_data(self.entry)['metadata']['json-ld']
        )

    def test_schema_has_no_supervisor_field(self):
        """The schema should not have NOT translated supervisor field"""
        self.assertNotIn(
            'role_supervisor',
            self.inner_schema.fields
        )

    def test_correct_translated_supervisor_value_in_generated_data(self):
        """No supervisor -> empty data"""
        self.assertEqual(
            [],
            self.translator.translate_data(self.entry)['metadata']['json-ld']['role:dgs']
        )

    def test_schema_validation(self):
        inner_errors = self.phaidra_errors['metadata']['json-ld']
        self.assertIn('role:dgs', inner_errors)
        self.assertEqual(
            inner_errors['role:dgs'],
            [MISSING_SUPERVISOR, ]
        )

    def test_error_translation(self):
        """There should be an missing supervisor error message in the translated errors"""
        errors = self.translator.translate_errors(self.phaidra_errors)
        self.assertIn('contributors', errors['data'])
        self.assertEqual(
            [MISSING_SUPERVISOR, ],
            errors['data']['contributors'],
        )

    def test_custom_validation_mechanism_added_in_schema(self):
        """The field should differ from other dynamic fields: required=True, validator=MissingSupervisorValidator"""
        self.assertEqual(len(self.inner_schema.custom_validation_callables), 1)
        self.assertEqual(self.inner_schema.custom_validation_callables[0].key, 'role:dgs')

    def test_schema_has_translated_supervisor_field(self):
        """The schema should have the dynamically translated supervisor field"""
        self.assertIn(
            'role_dgs',
            self.inner_schema.fields
        )
