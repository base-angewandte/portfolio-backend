from pathlib import Path
from typing import Dict, Optional, Set, List

import marshmallow

from media_server.archiver.implementations.phaidra.abstracts.datatranslation import AbstractDataTranslator
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import ConceptMapper
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

    def _get_file_name(self, media: Media) -> List[str]:
        if not media.file:
            return []
        path = Path(media.file.name)
        return [path.name, ]

    def _get_licenses(self, media: Media):
        phaidra_licenses = (
            [
                media.license['source'],
            ]
            if media.license
            else []
        )

        # one phaidra license can have multiple licenses in skosmos
        # but return a flat list
        return [
            translated_license
            for phaidra_license in phaidra_licenses
            for translated_license in self._translate_license(phaidra_license)
        ]

    def _translate_license(self, phaidra_license: str) -> Set[str]:
        concept_mapper = ConceptMapper.from_base_uri(phaidra_license, set())
        return concept_mapper.owl_sameAs
