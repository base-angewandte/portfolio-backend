"""Each of these test cases represent one rule.

The different methods represent various stages in the lifecycle of the
request, either in validation fail or success.
"""
from rest_framework.exceptions import ValidationError

from django.test import TestCase

from media_server.archiver.controller.default import DefaultArchiveController
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
    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        cls.client_provider = ClientProvider(cls.model_provider)

    """
    https://basedev.uni-ak.ac.at/redmine/issues/1419

    > The entry must have at least one author.
    """

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
        media = self.model_provider.get_media(author=False)
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
        media = self.model_provider.get_media(author=True)
        controller = DefaultArchiveController(
            media.owner,
            {
                media.id,
            },
        )
        self.assertIsNone(controller.validate())

    def test_endpoint_validation_fail(self):
        media = self.model_provider.get_media(author=False)
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
        media = self.model_provider.get_media(author=True)
        response = self.client_provider.get_media_primary_key_response(media)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Asset validation successful')
