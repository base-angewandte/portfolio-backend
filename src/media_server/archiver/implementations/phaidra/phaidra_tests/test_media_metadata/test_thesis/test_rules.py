"""Each of these test cases represent one rule.

The different methods represent various stages in the lifecycle of the
request, either in validation fail or success.
"""
from rest_framework.exceptions import ValidationError

from django.test import TestCase

from media_server.archiver.controller.default import DefaultArchiveController
from media_server.archiver.implementations.phaidra.metadata.default.schemas import (
    get_phaidra_meta_data_schema_with_dynamic_fields,
)
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    BidirectionalConceptsMapper,
)
from media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation import (
    PhaidraThesisMetaDataTranslator,
)
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import _PhaidraThesisMetaDataSchema
from media_server.archiver.implementations.phaidra.phaidra_tests.test_media_metadata.test_thesis.utillities import (
    ClientProvider,
    ModelProvider,
    PhaidraContainerGenerator,
)


class AtLeastOneAuthorTestCase(TestCase):
    """https://basedev.uni-ak.ac.at/redmine/issues/1419.

    > The entry must have at least one author.
    """

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    expected_phaidra_error = {
        'role:aut': [
            'Shorter than minimum length 1.',
        ]
    }

    expected_portfolio_errors = {
        'data': {
            'authors': [
                'Shorter than minimum length 1.',
            ],
        },
    }

    def test_schema_validation_fail(self):
        invalid_data = PhaidraContainerGenerator.create_phaidra_container(respect_author_rule=False)
        # no need for the dynamic schema here
        static_schema = _PhaidraThesisMetaDataSchema()
        errors = static_schema.validate(invalid_data)
        self.assertEqual(errors, self.expected_phaidra_error)

    def test_schema_validation(self):
        valid_data = PhaidraContainerGenerator.create_phaidra_container(respect_author_rule=True)
        # no need for the dynamic schema here
        static_schema = _PhaidraThesisMetaDataSchema()
        errors = static_schema.validate(valid_data)
        self.assertEqual({}, errors)

    def test_error_transformation(self):
        translator = PhaidraThesisMetaDataTranslator()
        # no need to test dynamic here
        portfolio_errors = translator._translate_errors_with_static_structure(self.expected_phaidra_error)
        self.assertEqual(self.expected_portfolio_errors, portfolio_errors)

    def test_implementation_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(author=False))
        controller = DefaultArchiveController(
            media.owner,
            {
                media.id,
            },
        )
        self.assertRaisesMessage(
            ValidationError,
            # This is str repr and not the exactly same as in the response
            "{'data': {'authors': [ErrorDetail(string='Shorter than minimum length 1.', code='invalid')]}}",
            lambda: controller.validate(),
        )

    def test_implementation(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(author=True))
        controller = DefaultArchiveController(
            media.owner,
            {
                media.id,
            },
        )
        self.assertIsNone(controller.validate())

    def test_endpoint_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(author=False))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'data': {
                    'authors': [
                        'Shorter than minimum length 1.',
                    ]
                }
            },
        )

    def test_endpoint(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(author=True))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Asset validation successful')


class MustHaveALanguageTestCase(TestCase):
    """https://basedev.uni-ak.ac.at/redmine/issues/1419.

    > The entry must have a language.
    """

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    expected_phaidra_errors = {
        'dcterms:language': [
            'Shorter than minimum length 1.',
        ]
    }

    expected_portfolio_errors = {
        'data': {
            'language': [
                'Missing data for required field.',
            ]
        }
    }

    def test_schema_validation_fail(self):
        invalid_data = PhaidraContainerGenerator.create_phaidra_container(respect_language_rule=False)
        # no need for the dynamic schema here
        static_schema = _PhaidraThesisMetaDataSchema()
        errors = static_schema.validate(invalid_data)
        self.assertEqual(errors, self.expected_phaidra_errors)

    def test_schema_validation(self):
        valid_data = PhaidraContainerGenerator.create_phaidra_container(respect_language_rule=True)
        # no need for the dynamic schema here
        static_schema = _PhaidraThesisMetaDataSchema()
        errors = static_schema.validate(valid_data)
        self.assertEqual(errors, {})

    def test_error_transformation(self):
        translator = PhaidraThesisMetaDataTranslator()
        # no need to test dynamic here
        portfolio_errors = translator._translate_errors_with_static_structure(self.expected_phaidra_errors)
        self.assertEqual(self.expected_portfolio_errors, portfolio_errors)

    def test_implementation_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(german_language=False))
        controller = DefaultArchiveController(
            media.owner,
            {
                media.id,
            },
        )
        self.assertRaisesMessage(
            ValidationError,
            # This is str repr and not the exactly same as in the response
            "{'data': {'language': [ErrorDetail(string='Missing data for required field.', code='invalid')]}}",
            lambda: controller.validate(),
        )

    def test_implementation(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(german_language=True))
        controller = DefaultArchiveController(
            media.owner,
            {
                media.id,
            },
        )
        self.assertIsNone(controller.validate())

    def test_endpoint_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(german_language=False))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'data': {
                    'language': [
                        'Missing data for required field.',
                    ]
                }
            },
        )

    def test_endpoint(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(german_language=True))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Asset validation successful')


class MustHaveAnAdviserTestCase(TestCase):
    """https://basedev.uni-ak.ac.at/redmine/issues/1419.

    > The container must have an advisor.
    """

    expected_phaidra_errors_missing_field = {
        'role:supervisor': {
            0: {
                'skos:exactMatch': {0: {'@value': ['Missing data for required field.']}},
                'schema:name': {0: {'@value': ['Missing data for required field.']}},
            }
        }
    }

    expected_phaidra_errors_empty_field = {
        'role:supervisor': [
            'Shorter than minimum length 1.',
        ]
    }

    expected_portfolio_errors = {
        'data': {
            'contributors': [
                'At least one contributor has to have the role advisor.',
            ],
        }
    }

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    def test_schema_validation_fail_missing(self):
        invalid_data = PhaidraContainerGenerator.create_phaidra_container(respect_contributor_role=False)
        # Need dynamic schema here (!)
        entry = self.model_provider.get_entry(advisor=False)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_schema = get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=mapping, base_schema_class=_PhaidraThesisMetaDataSchema
        )
        errors = dynamic_schema.validate(invalid_data)
        self.assertEqual(errors, self.expected_phaidra_errors_missing_field)

    def test_schema_validation_fail_empty(self):
        data = PhaidraContainerGenerator.create_phaidra_container(respect_contributor_role=True)
        data['role:supervisor'] = []
        # Need dynamic schema here (!)
        entry = self.model_provider.get_entry(advisor=True)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_schema = get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=mapping, base_schema_class=_PhaidraThesisMetaDataSchema
        )
        errors = dynamic_schema.validate(data)
        self.assertEqual(errors, self.expected_phaidra_errors_empty_field)

    def test_schema_validation(self):
        valid_data = PhaidraContainerGenerator.create_phaidra_container(respect_contributor_role=True)
        # Need dynamic schema here (!)
        entry = self.model_provider.get_entry(advisor=True)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_schema = get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=mapping, base_schema_class=_PhaidraThesisMetaDataSchema
        )
        errors = dynamic_schema.validate(valid_data)
        self.assertEqual({}, errors)

    def test_error_transformation_missing_field(self):
        translator = PhaidraThesisMetaDataTranslator()
        # Need to test dynamic here
        entry = self.model_provider.get_entry(advisor=True)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        portfolio_errors = translator.translate_errors(self.expected_phaidra_errors_missing_field, mapping)
        self.assertEqual(
            portfolio_errors,
            self.expected_portfolio_errors,
        )

    def test_error_transformation_empty_field(self):
        translator = PhaidraThesisMetaDataTranslator()
        # Need to test dynamic here
        entry = self.model_provider.get_entry(advisor=True)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        portfolio_errors = translator.translate_errors(self.expected_phaidra_errors_empty_field, mapping)
        self.assertEqual(self.expected_portfolio_errors, portfolio_errors)

    def test_implementation_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(advisor=False))
        controller = DefaultArchiveController(
            media.owner,
            {
                media.id,
            },
        )
        self.assertRaisesMessage(
            ValidationError,
            # This is str repr and not the exactly same as in the response
            "{'data': {'contributors': [ErrorDetail(string='At least one contributor has to have the role advisor.',"
            " code='invalid')]}}",
            lambda: controller.validate(),
        )

    def test_implementation(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(advisor=True))
        controller = DefaultArchiveController(
            media.owner,
            {
                media.id,
            },
        )
        self.assertIsNone(controller.validate())

    def test_endpoint_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(advisor=False))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'data': {
                    'contributors': [
                        'At least one contributor has to have the role advisor.',
                    ]
                }
            },
        )

    def test_endpoint(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(advisor=True))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Asset validation successful')


class EmptyThesisTestCase(TestCase):
    """In the case of an entry, with thesis, but not input, all error messages
    should be displayed."""

    expected_phaidra_errors_missing_field = {
        'role:aut': ['Shorter than minimum length 1.'],
        'role:supervisor': {
            0: {
                'schema:name': {0: {'@value': ['Missing data for required field.']}},
                'skos:exactMatch': {0: {'@value': ['Missing data for required field.']}},
            }
        },
        'dcterms:language': ['Shorter than minimum length 1.'],
        'bf:note': [
            'Thesis must include at least one english abstract.',
            'Thesis must include at least one german abstract.',
        ],
    }

    expected_portfolio_errors = {
        'data': {
            'language': ['Missing data for required field.'],
            'authors': ['Shorter than minimum length 1.'],
            'contributors': ['At least one contributor has to have the role advisor.'],
        },
        'texts': [
            'Thesis must include at least one english abstract.',
            'Thesis must include at least one german abstract.',
        ],
    }

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    def test_schema_validation_fail(self):
        invalid_data = PhaidraContainerGenerator.create_phaidra_container(
            respect_contributor_role=False,
            respect_language_rule=False,
            respect_author_rule=False,
            respect_english_abstract_rule=False,
            respect_german_abstract_rule=False,
        )
        # Need dynamic schema here (!)
        entry = self.model_provider.get_entry(
            advisor=False, author=False, german_language=False, english_abstract=False, german_abstract=False
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_schema = get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=mapping, base_schema_class=_PhaidraThesisMetaDataSchema
        )
        errors = dynamic_schema.validate(invalid_data)
        self.assertEqual(errors, self.expected_phaidra_errors_missing_field)

    def test_error_transformation(self):
        translator = PhaidraThesisMetaDataTranslator()
        # Need to test dynamic here
        entry = self.model_provider.get_entry(
            advisor=False, author=False, german_language=False, english_abstract=False, german_abstract=False
        )
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        portfolio_errors = translator.translate_errors(self.expected_phaidra_errors_missing_field, mapping)
        self.assertEqual(
            portfolio_errors,
            self.expected_portfolio_errors,
        )

    def test_endpoint_validation_fail(self):
        media = self.model_provider.get_media(
            self.model_provider.get_entry(
                advisor=False, author=False, german_language=False, english_abstract=False, german_abstract=False
            )
        )
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            self.expected_portfolio_errors,
        )


class MustHaveEnglishAbstractTestCase(TestCase):

    expected_phaidra_errors_missing_field = {
        'bf:note': [
            'Thesis must include at least one english abstract.',
        ]
    }

    expected_portfolio_errors = {
        'texts': [
            'Thesis must include at least one english abstract.',
        ]
    }

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    def test_schema_validation_fail(self):
        invalid_data = PhaidraContainerGenerator.create_phaidra_container(respect_english_abstract_rule=False)
        entry = self.model_provider.get_entry(english_abstract=False)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_schema = get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=mapping, base_schema_class=_PhaidraThesisMetaDataSchema
        )
        errors = dynamic_schema.validate(invalid_data)
        self.assertEqual(errors, self.expected_phaidra_errors_missing_field)

    def test_error_transformation(self):
        translator = PhaidraThesisMetaDataTranslator()
        entry = self.model_provider.get_entry(english_abstract=False)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        portfolio_errors = translator.translate_errors(self.expected_phaidra_errors_missing_field, mapping)
        self.assertEqual(
            portfolio_errors,
            self.expected_portfolio_errors,
        )

    def test_endpoint_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(english_abstract=False))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            self.expected_portfolio_errors,
        )


class MustHaveGermanAbstractTestCase(TestCase):

    expected_phaidra_errors_missing_field = {
        'bf:note': [
            'Thesis must include at least one german abstract.',
        ]
    }

    expected_portfolio_errors = {
        'texts': [
            'Thesis must include at least one german abstract.',
        ]
    }

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    def test_schema_validation_fail(self):
        invalid_data = PhaidraContainerGenerator.create_phaidra_container(respect_german_abstract_rule=False)
        entry = self.model_provider.get_entry(german_abstract=False)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        dynamic_schema = get_phaidra_meta_data_schema_with_dynamic_fields(
            bidirectional_concepts_mapper=mapping, base_schema_class=_PhaidraThesisMetaDataSchema
        )
        errors = dynamic_schema.validate(invalid_data)
        self.assertEqual(errors, self.expected_phaidra_errors_missing_field)

    def test_error_transformation(self):
        translator = PhaidraThesisMetaDataTranslator()
        entry = self.model_provider.get_entry(german_abstract=False)
        mapping = BidirectionalConceptsMapper.from_entry(entry)
        portfolio_errors = translator.translate_errors(self.expected_phaidra_errors_missing_field, mapping)
        self.assertEqual(
            portfolio_errors,
            self.expected_portfolio_errors,
        )

    def test_endpoint_validation_fail(self):
        media = self.model_provider.get_media(self.model_provider.get_entry(german_abstract=False))
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            self.expected_portfolio_errors,
        )
