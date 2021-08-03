import json

from jsonschema import Draft4Validator

from django.forms.models import model_to_dict
from django.test import TestCase

from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider


class MetaDataPortfolioTestCase(TestCase):
    """According to frontend devs, title is not found in not thesis
    metadata."""

    @classmethod
    def setUpTestData(cls):
        cls.model_provider = ModelProvider()
        with open(
            'media_server/archiver/implementations/phaidra/'
            'phaidra_tests/test_media_metadata/metadata-schema-portfolio.json'
        ) as file:
            cls.validator = Draft4Validator(json.load(file))

    def test_thesis(self):
        entry = self.model_provider.get_entry()
        self.assertTrue(self.validator.is_valid(model_to_dict(entry)))

    def test_not_thesis(self):
        entry = self.model_provider.get_entry(thesis_type=False)
        self.assertTrue(self.validator.is_valid(model_to_dict(entry)))
