import unittest

from media_server.archiver.implementations.phaidra.media.datatranslation import translator
from media_server.archiver.implementations.phaidra.media.schemas import PhaidraMediaData
from media_server.models import Media


class PhaidraTestCase(unittest.TestCase):
    def test_media_data_translation(self):
        media = Media(file='./myfile', mime_type='anything', license={'source': 'whatever'})

        data = translator.translate(media)
        schema = PhaidraMediaData()
        errors = schema.load(data).errors
        self.assertEqual(errors, {})
        self.assertEqual(translator.translate(errors, from_source_to_target=False), None)

    def test_media_data_error_translation(self):
        media = Media(
            file='./myfile',
            mime_type='anything',
            # missing! license={'source': 'whatever'}
        )

        data = translator.translate(media)
        schema = PhaidraMediaData()
        errors = schema.load(data).errors
        self.assertEqual(errors, {'metadata': {'json-ld': {'edm:rights': ['Missing data for required field.']}}})
        self.assertEqual(
            translator.translate(errors, from_source_to_target=False).as_dict(),
            {'license': {'source': ['Missing data for required field.']}},
        )
