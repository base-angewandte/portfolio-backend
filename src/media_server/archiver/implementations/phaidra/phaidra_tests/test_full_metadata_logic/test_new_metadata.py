"""
New metadata is added to the containers. Check it
"""

from django.test import TestCase

from media_server.archiver.implementations.phaidra.metadata.default.schemas import PhaidraMetaData, \
    ValueLanguageBaseSchema
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import create_dynamic_phaidra_thesis_meta_data_schema
from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import FakeBidirectionalConceptsMapper
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider
from media_server.archiver.implementations.phaidra.utillities.fields import PortfolioNestedField


class TestFeature1677(TestCase):
    # Test this data
    translated_data_with_one_location: dict
    translated_data_with_no_location: dict
    translated_data_with_two_locations: dict
    validation_with_one_location: dict
    validation_with_no_location: dict
    validation_with_two_locations: dict

    # Use this data to test
    location_label_1 = 'Universität für Angewandte Kunst Wien'
    location_label_2 = 'Wien, Österreich'

    location_1_portfolio = {'country': 'Austria',
                            'geometry': {'coordinates': [16.348388, 48.198674], 'type': 'Point'},
                            'label': location_label_1,
                            'locality': 'Vienna',
                            'region': 'Wien',
                            'source': 'https://api.geocode.earth/v1/place?ids=whosonfirst:locality:101748073'
                            }

    location_2_portfolio = {'country': 'Österreich',
                            'geometry': {'coordinates': [16.382464, 48.208126], 'type': 'Point'},
                            'house_number': '2',
                            'label': location_label_2,
                            'locality': 'Wien',
                            'postcode': '1010',
                            'region': 'Wien',
                            'source': 'https://api.geocode.earth/v1/place?ids=openstreetmap:venue:way/25427674',
                            'street': 'Oskar-Kokoschka-Platz'}

    # Expected data

    location_1_phaidra = {
        '@value': location_label_1,
        '@language': 'und',
    }

    location_2_phaidra = {
        '@value': location_label_2,
        '@language': 'und',
    }

    @classmethod
    def setUpTestData(cls):
        """
        1) Set up data and validation with location
        2) Set up data and validation without location
        2) Set up data and validation with two locations
        :return:
        """
        model_provider = ModelProvider()

        entry_with_no_location = model_provider.get_entry(thesis_type=False)

        entry_with_one_location = model_provider.get_entry(thesis_type=False)
        entry_with_one_location.data['locations'] = [cls.location_1_portfolio, ]
        entry_with_one_location.save()
        entry_with_one_location.refresh_from_db()

        entry_with_two_locations = model_provider.get_entry(thesis_type=False)
        entry_with_two_locations.data['locations'] = [cls.location_1_portfolio, cls.location_2_portfolio]
        entry_with_two_locations.save()
        entry_with_two_locations.refresh_from_db()

        mapping_with_no_location = FakeBidirectionalConceptsMapper.from_entry(entry_with_no_location)
        mapping_with_one_location = FakeBidirectionalConceptsMapper.from_entry(entry_with_one_location)
        mapping_with_two_locations = FakeBidirectionalConceptsMapper.from_entry(entry_with_two_locations)

        # noinspection PyTypeChecker
        translator_0_locations = PhaidraMetaDataTranslator(mapping_with_no_location)
        # noinspection PyTypeChecker
        translator_1_location = PhaidraMetaDataTranslator(mapping_with_one_location)
        # noinspection PyTypeChecker
        translator_2_locations = PhaidraMetaDataTranslator(mapping_with_two_locations)

        schema_0_locations = PhaidraMetaData()
        schema_1_location = PhaidraMetaData()
        schema_2_locations = PhaidraMetaData()

        cls.translated_data_with_no_location = translator_0_locations.translate_data(entry_with_no_location)
        cls.translated_data_with_one_location = translator_1_location.translate_data(entry_with_one_location)
        cls.translated_data_with_two_locations = translator_2_locations.translate_data(entry_with_two_locations)

        cls.validation_with_no_location = schema_0_locations.validate(cls.translated_data_with_no_location)
        cls.validation_with_one_location = schema_1_location.validate(cls.translated_data_with_one_location)
        cls.validation_with_two_locations = schema_2_locations.validate(cls.translated_data_with_two_locations)

        # Also check that the schemas check the correct form of the data
        cls.normal_schema = PhaidraMetaData()
        # noinspection PyTypeChecker
        cls.thesis_schema = create_dynamic_phaidra_thesis_meta_data_schema(
            FakeBidirectionalConceptsMapper.from_entry(entry_with_no_location)
        )

    def test_translated_data(self):
        self.assertIn('bf:physicalLocation', self.translated_data_with_no_location['metadata']['json-ld'])
        self.assertIn('bf:physicalLocation', self.translated_data_with_one_location['metadata']['json-ld'])
        self.assertIn('bf:physicalLocation', self.translated_data_with_two_locations['metadata']['json-ld'])

        self.assertEqual([], self.translated_data_with_no_location['metadata']['json-ld']['bf:physicalLocation'])
        self.assertEqual(
            [self.location_1_phaidra, ],
            self.translated_data_with_one_location['metadata']['json-ld']['bf:physicalLocation']
        )
        self.assertEqual(
            [self.location_1_phaidra, self.location_2_phaidra],
            self.translated_data_with_two_locations['metadata']['json-ld']['bf:physicalLocation']
        )

    def test_validation(self):
        self.assertEqual({}, self.validation_with_no_location)
        self.assertEqual({}, self.validation_with_two_locations)
        self.assertEqual({}, self.validation_with_two_locations)

    def test_schema_contains_location_fields(self):
        # There is a schema …
        self.assertIn(
            'bf_physicalLocation',
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields
        )
        self.assertIn(
            'bf_physicalLocation',
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields
        )
        # It checks for an array of objects
        self.assertIsInstance(
            PortfolioNestedField,
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation']
        )
        self.assertIsInstance(
            PortfolioNestedField,
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation']
        )
        # And checks for objects of the correct type
        self.assertIsInstance(
            ValueLanguageBaseSchema,
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation'].nested
        )

        self.assertIsInstance(
            ValueLanguageBaseSchema,
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation'].nested
        )
