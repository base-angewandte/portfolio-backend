"""
New metadata is added to the containers. Check it
"""
import IPython
import requests as requests
from django.test import TestCase

from media_server.archiver.implementations.phaidra.metadata.default.schemas import PhaidraMetaData, \
    ValueLanguageBaseSchema
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import create_dynamic_phaidra_thesis_meta_data_schema
from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import FakeBidirectionalConceptsMapper, \
    ClientProvider
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
    phaidra_data_with_1_location: dict
    phaidra_data_with_2_locations: dict

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
        entry_with_one_location.data['location'] = [cls.location_1_portfolio, ]
        entry_with_one_location.save()
        entry_with_one_location.refresh_from_db()

        entry_with_two_locations = model_provider.get_entry(thesis_type=False)
        entry_with_two_locations.data['location'] = [cls.location_1_portfolio, cls.location_2_portfolio]
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

        # Additional full API-User Test:
        media_with_one_location = model_provider.get_media(entry_with_one_location)
        media_with_two_locations = model_provider.get_media(entry_with_two_locations)
        client = ClientProvider(model_provider)
        for media in (media_with_one_location, media_with_two_locations):
            response = client.get_media_primary_key_response(media, only_validate=False)
            if response.status_code != 200:
                raise RuntimeError(f'Can not perform test. Archival failed {response.status_code} {response.content}')
        entry_with_one_location.refresh_from_db()
        entry_with_two_locations.refresh_from_db()
        phaidra_responses = [
            requests.get(f'https://services.phaidra-sandbox.univie.ac.at/api/object/{entry.archive_id}/jsonld')
            for entry in (entry_with_one_location, entry_with_two_locations)
        ]
        for response in phaidra_responses:
            if response.status_code != 200:
                raise RuntimeError(f'Can not perform test. Phaidra returned {response.status_code} {response.content}')
        phaidra_data = [response.json() for response in phaidra_responses]
        cls.phaidra_data_with_1_location, cls.phaidra_data_with_2_locations = phaidra_data

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
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation'],
            PortfolioNestedField,
        )
        self.assertIsInstance(
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation'],
            PortfolioNestedField,
        )
        # And checks for objects of the correct type
        self.assertIs(
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation'].nested,
            ValueLanguageBaseSchema,
        )

        self.assertIs(
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['bf_physicalLocation'].nested,
            ValueLanguageBaseSchema,
        )

    def test_phaidra(self):
        self.assertIn(
            'bf:physicalLocation',
            self.phaidra_data_with_1_location
        )
        self.assertIn(
            'bf:physicalLocation',
            self.phaidra_data_with_2_locations
        )
        self.assertEqual(
            [self.location_1_phaidra, ],
            self.phaidra_data_with_1_location['bf:physicalLocation']
        )
        self.assertEqual(
            [self.location_1_phaidra, self.location_2_phaidra ],
            self.phaidra_data_with_2_locations['bf:physicalLocation']
        )