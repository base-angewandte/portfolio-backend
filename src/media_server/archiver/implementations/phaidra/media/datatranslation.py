from typing import Any, Dict, Hashable, List, Optional

from media_server.models import Media


class PhaidraMediaDataTranslator:
    def translate_data(self, media: Media) -> dict:
        return {
            'metadata': {
                'json-ld': {
                    'ebucore:hasMimeType': self._get_media_mime_types(media),
                    'ebucore:filename': self._get_file_name(media),
                    'edm:rights': self._get_licenses(media),
                }
            }
        }

    def translate_errors(self, errors: Optional[Dict]) -> Dict:
        translated_errors = {}
        if (errors is None) or len(errors) == 0:
            return translated_errors
        try:
            translated_errors = self.set_nested(
                ['media', 'mime_type'], errors['metadata']['json-ld']['ebucore:hasMimeType'], translated_errors
            )
        except KeyError:
            pass
        try:
            translated_errors = self.set_nested(
                ['media', 'file', 'name'], errors['metadata']['json-ld']['ebucore:filename'], translated_errors
            )
        except KeyError:
            pass
        try:
            translated_errors = self.set_nested(
                ['media', 'license', 'source'], errors['metadata']['json-ld']['edm:rights'], translated_errors
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

    def set_nested(self, keys: List[Hashable], value: Any, target: Dict) -> Dict:
        if len(keys) == 0:
            return target
        sub_target = target
        last_key = keys.pop()
        for key in keys:
            if key not in sub_target:
                sub_target[key] = {}
            sub_target = sub_target[key]
        sub_target[last_key] = value
        return target
