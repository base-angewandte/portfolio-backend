from typing import Dict, List, Set

from marshmallow import ValidationError, fields, validate, validates

from media_server.archiver.implementations.phaidra.metadata.default.schemas import (
    PersonSchema,
    SkosConceptSchema,
    _PhaidraMetaData,
)


class _PhaidraThesisMetaDataSchema(_PhaidraMetaData):
    role_aut = fields.Nested(
        PersonSchema, many=True, validate=validate.Length(min=1), load_from='role:aut', dump_to='role:aut'
    )

    dcterms_language = fields.Nested(
        SkosConceptSchema,
        many=True,
        load_from='dcterms:language',
        dump_to='dcterms:language',
        validate=validate.Length(min=1),
        required=True,
    )

    role_supervisor = fields.Nested(
        PersonSchema,
        many=True,
        load_from='role:supervisor',
        dump_to='role:supervisor',
        validate=validate.Length(min=1),
        required=True,
    )

    @validates('bf_note')
    def must_have_an_english_and_german_abstract(self, field_data: List[Dict]):
        abstracts = self._filter_type_label_schemas(field_data, type_='bf:Summary')
        languages = self._extract_languages_from_type_label_schemas(abstracts)
        errors = []
        if 'eng' not in languages:
            errors.append('Thesis must include at least one english abstract.')
        if 'deu' not in languages:
            errors.append('Thesis must include at least one german abstract.')
        if errors:
            raise ValidationError(errors)

    def _filter_type_label_schemas(self, type_label_schemas: List[Dict], type_: str) -> List[Dict]:
        return [
            type_label_schema
            for type_label_schema in type_label_schemas
            if ('type' in type_label_schema) and (type_label_schema['type'] == type_)
        ]

    def _extract_languages_from_type_label_schemas(self, type_label_schemas: List[Dict]) -> Set:
        return {
            label['language']
            for type_label_schema in type_label_schemas
            for label in type_label_schema['skos_prefLabel']
        }
