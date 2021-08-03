from typing import Dict, Optional

import marshmallow

from media_server.archiver.implementations.phaidra.abstracts.datatranslation import AbstractDataTranslator
from media_server.models import Media


class PhaidraMediaDataTranslator(AbstractDataTranslator):
    def translate_data(self, media: Media) -> dict:
        return {
            'metadata': {
                'json-ld': {
                    'ebucore:filename': self._get_file_name(media),
                    'edm:rights': self._get_licenses(media),
                }
            }
        }

    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        super().translate_errors(errors)
        translated_errors = {}
        try:
            mime_errors = errors['metadata']['json-ld']['ebucore:hasMimeType']
            mime_errors = [
                marshmallow.fields.Field.default_error_messages['required']
                if 'Shorter than minimum length' in mime_error
                else mime_error
                for mime_error in mime_errors
            ]
            translated_errors = self.set_nested(['media', 'mime_type'], mime_errors, translated_errors)
        except KeyError:
            pass
        try:
            translated_errors = self.set_nested(
                ['media', 'file', 'name'], errors['metadata']['json-ld']['ebucore:filename'], translated_errors
            )
        except KeyError:
            pass
        try:
            license_errors = errors['metadata']['json-ld']['edm:rights']
            license_errors = [
                marshmallow.fields.Field.default_error_messages['required']
                if 'Shorter than minimum length' in license_error
                else license_error
                for license_error in license_errors
            ]
            translated_errors = self.set_nested(
                [
                    'media',
                    'license',
                ],
                license_errors,
                translated_errors,
            )
        except KeyError:
            pass
        return translated_errors

    def _get_media_mime_types(self, media: Media):
        return (
            [
                media.mime_type,
            ]
            if media.mime_type
            else []
        )

    def _get_file_name(self, media: Media):
        return (
            [
                media.file.name,
            ]
            if media.file
            else []
        )

    def _get_licenses(self, media: Media):
        return (
            [
                media.license['source'],
            ]
            if media.license
            else []
        )
