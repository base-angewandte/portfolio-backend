"""
New metadata is added to the containers. Check it
"""
import requests as requests
from django.test import TestCase

from core.models import Entry
from media_server.archiver.implementations.phaidra.metadata.default.schemas import PhaidraMetaData, \
    ValueLanguageBaseSchema, RdfSeeAlsoSchema
from media_server.archiver.implementations.phaidra.metadata.thesis.schemas import \
    create_dynamic_phaidra_thesis_meta_data_schema, PhaidraThesisMetaData
from media_server.archiver.implementations.phaidra.metadata.default.datatranslation import PhaidraMetaDataTranslator, \
    _convert_two_to_three_letter_language_code, BfNoteTranslator
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import FakeBidirectionalConceptsMapper, \
    ClientProvider
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider
from media_server.archiver.implementations.phaidra.utillities.fields import PortfolioNestedField
from media_server.archiver.interface.exceptions import InternalValidationError
from media_server.models import Media


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
            [self.location_1_phaidra, self.location_2_phaidra],
            self.phaidra_data_with_2_locations['bf:physicalLocation']
        )


class TestFeature1678(TestCase):
    """
    https://basedev.uni-ak.ac.at/redmine/issues/1678



    URL - not currently mapped, map to rdfs:seeAlso

    https://github.com/phaidra/phaidra-ld/wiki/Metadata-fields#see-also

    """
    # Test this data
    translated_data_0_url: dict
    translated_data_1_url: dict
    validation_0_url: dict
    validation_1_url: dict
    phaidra_data_0_url: dict
    phaidra_data_1_url: dict
    normal_schema: PhaidraMetaData
    thesis_schema: PhaidraThesisMetaData

    # Constant test data
    url = 'http://example.com/'
    expected_phaidra_data_0_url = []
    expected_phaidra_data_1_url = [
        {
            "@type": "schema:URL",
            "schema:url": [url, ],
            "skos:prefLabel": [
                {
                    "@value": url,
                    "@language": "und"
                }
            ]
        },
    ]

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()

        entry_0_url = model_provider.get_entry(thesis_type=False)

        entry_1_url = model_provider.get_entry(thesis_type=False)
        entry_1_url.data['url'] = cls.url
        entry_1_url.save()
        entry_1_url.refresh_from_db()

        mapping_0_url = FakeBidirectionalConceptsMapper.from_entry(entry_0_url)
        mapping_1_url = FakeBidirectionalConceptsMapper.from_entry(entry_1_url)

        # noinspection PyTypeChecker
        cls.translated_data_0_url = PhaidraMetaDataTranslator(mapping_0_url).translate_data(entry_0_url)
        # noinspection PyTypeChecker
        cls.translated_data_1_url = PhaidraMetaDataTranslator(mapping_1_url).translate_data(entry_1_url)

        cls.validation_0_url = PhaidraMetaData().validate(cls.translated_data_0_url)
        cls.validation_1_url = PhaidraMetaData().validate(cls.translated_data_1_url)

        cls.normal_schema = PhaidraMetaData()
        # noinspection PyTypeChecker
        cls.thesis_schema = create_dynamic_phaidra_thesis_meta_data_schema(
            FakeBidirectionalConceptsMapper.from_entry(entry_0_url)
        )
        entries = (entry_0_url, entry_1_url)
        media_objects = [model_provider.get_media(entry) for entry in entries]
        client = ClientProvider(model_provider)
        portfolio_responses = [client.get_media_primary_key_response(media, False) for media in media_objects]
        if any([response.status_code != 200 for response in portfolio_responses]):
            raise RuntimeError(
                f'Could not archive assets: ' +
                '\n'.join((f'{response.status_code} {response.content}'
                           for response in portfolio_responses
                           if response.status_code != 200
                           )
                          )
            )
        for entry in entries:
            entry.refresh_from_db()

        phaidra_responses = [
            requests.get(f'https://services.phaidra-sandbox.univie.ac.at/api/object/{entry.archive_id}/jsonld')
            for entry in entries
        ]

        if any([response.status_code != 200 for response in phaidra_responses]):
            raise RuntimeError(
                f'Could not archive assets: ' +
                '\n'.join((f'{response.status_code} {response.content}'
                           for response in phaidra_responses
                           if response.status_code != 200
                           )
                          )
            )

        phaidra_data = [response.json() for response in phaidra_responses]

        cls.phaidra_data_0_url, cls.phaidra_data_1_url = phaidra_data

    def test_translated_data(self):
        self.assertIn('rdfs:seeAlso', self.translated_data_0_url['metadata']['json-ld'])
        self.assertIn('rdfs:seeAlso', self.translated_data_1_url['metadata']['json-ld'])
        self.assertEqual([], self.translated_data_0_url['metadata']['json-ld']['rdfs:seeAlso'])
        self.assertEqual(self.expected_phaidra_data_1_url,
                         self.translated_data_1_url['metadata']['json-ld']['rdfs:seeAlso']
                         )

    def test_validation(self):
        self.assertEqual({}, self.validation_0_url)
        self.assertEqual({}, self.validation_1_url)

    def test_schema(self):
        # There is a schema …
        self.assertIn(
            'rdfs_seeAlso',
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields
        )
        self.assertIn(
            'rdfs_seeAlso',
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields
        )
        # It checks for an array of objects
        self.assertIsInstance(
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['rdfs_seeAlso'],
            PortfolioNestedField,
        )
        self.assertIsInstance(
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['rdfs_seeAlso'],
            PortfolioNestedField,
        )
        # And checks for objects of the correct type
        self.assertIs(
            RdfSeeAlsoSchema,
            self.normal_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['rdfs_seeAlso'].nested,
        )

        self.assertIs(
            RdfSeeAlsoSchema,
            self.thesis_schema.fields['metadata'].nested.fields['json_ld'].nested.fields['rdfs_seeAlso'].nested,
        )

    def test_phaidra(self):
        self.assertIn(
            'rdfs:seeAlso',
            self.phaidra_data_0_url
        )
        self.assertIn(
            'rdfs:seeAlso',
            self.phaidra_data_1_url
        )
        self.assertEqual(
            self.expected_phaidra_data_0_url,
            self.phaidra_data_0_url['rdfs:seeAlso']
        )
        self.assertEqual(
            self.expected_phaidra_data_1_url,
            self.phaidra_data_1_url['rdfs:seeAlso']
        )


class TestImprovement1686(TestCase):
    """
    https://basedev.uni-ak.ac.at/redmine/issues/1686

    1) If a language code can not be translated, default to und
    2) Do not skip records, where language codes can not be translated
    """

    def test_language_code_translation(self):
        """
        Unit test for 1) If a language code can not be translated, default to und
        """
        self.assertEqual('deu', _convert_two_to_three_letter_language_code('de'))
        self.assertEqual('eng', _convert_two_to_three_letter_language_code('en'))
        self.assertEqual('und', _convert_two_to_three_letter_language_code('unknown'))
        self.assertEqual('und', _convert_two_to_three_letter_language_code('xxx'))

    def test_bf_note_translation_known_language(self):
        """
        Integration test for both:
        1) If a language code can not be translated, default to und
        2) Do not skip records, where language codes can not be translated
        """
        entry = Entry(
            texts=[
                {
                    'data': [
                        {'text': 'Any Text', 'language': {'source': 'http://base.uni-ak.ac.at/portfolio/languages/en'}}
                    ]
                },
            ]
        )
        translator = BfNoteTranslator()
        data = translator.translate_data(entry)
        self.assertEqual(
            data,
            [
                {
                    '@type': 'bf:Note',
                    'skos:prefLabel': [
                        {
                            '@value': 'Any Text',
                            '@language': 'eng',
                        }
                    ],
                },
            ],
        )

    def test_bf_note_translation_unknown_language(self):
        """
        Integration test for both:
        1) If a language code can not be translated, default to und
        2) Do not skip records, where language codes can not be translated
        """
        entry = Entry(
            texts=[
                {
                    'data': [
                        {'text': 'Any Text', 'language': {'source': 'http://base.uni-ak.ac.at/portfolio/languages/xx'}}
                    ]
                },
            ]
        )
        translator = BfNoteTranslator()
        data = translator.translate_data(entry)
        self.assertEqual(
            data,
            [
                {
                    '@type': 'bf:Note',
                    'skos:prefLabel': [
                        {
                            '@value': 'Any Text',
                            '@language': 'und',
                        }
                    ],
                },
            ],
        )


class TestBug1693(TestCase):
    """
    https://basedev.uni-ak.ac.at/redmine/issues/1693

    At the time of writing tests, malformed urls from Entry.data['url'] will lead to an InternalServerError.

    Desired behavior is to throw a validation error, so that the user can correct the uri
    """

    translator: 'PhaidraMetaDataTranslator'
    media: 'Media'

    @classmethod
    def setUpTestData(cls):
        model_provider = ModelProvider()
        entry = model_provider.get_entry(thesis_type=False)
        entry.data['url'] = 'this is not a valid url'
        entry.save()
        entry.refresh_from_db()

        cls.media = model_provider.get_media(entry)

        mapper = FakeBidirectionalConceptsMapper.from_entry(entry)
        # noinspection PyTypeChecker
        cls.translator = PhaidraMetaDataTranslator(mapper)
        generated_data = cls.translator.translate_data(entry)
        # noinspection PyTypeChecker
        validator = create_dynamic_phaidra_thesis_meta_data_schema(mapper)
        cls.validation = validator.validate(generated_data)

        cls.custom_client = ClientProvider(model_provider)

    def test_validation_does_not_throw_internal_server_error(self):
        exception = None
        try:
            self.translator.translate_errors(self.validation)
        except InternalValidationError as error:
            exception = error
        self.assertNotIsInstance(exception, InternalValidationError)

    def test_validation_does_translate_validation_errors(self):
        errors = self.translator.translate_errors(self.validation)
        self.assertIn('data', errors)
        self.assertIn('url', errors['data'])
        self.assertEqual(['Not a valid URL.', ], errors['data']['url'])

    def test_server_returns_validation_errors(self):
        response = self.custom_client.get_media_primary_key_response(media=self.media, only_validate=True)
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            response.data,
            {
                'data': {
                    'url': ['Not a valid URL.', ]
                }
            }
        )