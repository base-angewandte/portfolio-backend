from typing import Dict, List, Set

from marshmallow import ValidationError, validates

from media_server.archiver.implementations.phaidra.metadata.default.schemas import (
    PersonSchema,
    SkosConceptSchema,
    _PhaidraMetaData,
)
from media_server.archiver.implementations.phaidra.utillities.fields import PortfolioNestedField
from media_server.archiver.implementations.phaidra.utillities.validate import (
    ValidateAuthor,
    ValidateLanguage,
    ValidateSupervisor,
)
from media_server.archiver.messages.validation.thesis import MISSING_ENGLISH_ABSTRACT, MISSING_GERMAN_ABSTRACT


class _PhaidraThesisMetaDataSchema(_PhaidraMetaData):
    role_aut = PortfolioNestedField(
        PersonSchema, many=True, validate=ValidateAuthor(), load_from='role:aut', dump_to='role:aut'
    )

    dcterms_language = PortfolioNestedField(
        SkosConceptSchema,
        many=True,
        load_from='dcterms:language',
        dump_to='dcterms:language',
        validate=ValidateLanguage(),
        required=True,
    )

    role_supervisor = PortfolioNestedField(
        PersonSchema,
        many=True,
        load_from='role:supervisor',
        dump_to='role:supervisor',
        validate=ValidateSupervisor(),
        required=True,
    )

    @validates('bf_note')
    def must_have_an_english_and_german_abstract(self, field_data: List[Dict]):
        abstracts = self._filter_type_label_schemas(field_data, type_='bf:Summary')
        languages = self._extract_languages_from_type_label_schemas(abstracts)
        errors = []
        if 'eng' not in languages:
            errors.append(MISSING_ENGLISH_ABSTRACT)
        if 'deu' not in languages:
            errors.append(MISSING_GERMAN_ABSTRACT)
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
