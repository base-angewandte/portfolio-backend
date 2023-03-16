from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from media_server.archiver.implementations.phaidra.metadata.thesis import must_use

if TYPE_CHECKING:
    from marshmallow.base import FieldABC

from marshmallow import Schema, ValidationError, fields, validates, validates_schema

from media_server.archiver.implementations.phaidra.metadata.default.schemas import (
    PersonSchema,
    PhaidraContainer,
    PhaidraMetaData,
    SkosConceptSchema,
)
from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    BidirectionalConceptsMapper,
    extract_phaidra_role_code,
)
from media_server.archiver.implementations.phaidra.utilities.fields import PortfolioNestedField
from media_server.archiver.implementations.phaidra.utilities.validate import (
    NotFalsyValidator,
    ValidateAuthor,
    ValidateLanguage,
)
from media_server.archiver.messages.validation.thesis import MISSING_ENGLISH_ABSTRACT, MISSING_GERMAN_ABSTRACT


class PhaidraThesisContainer(PhaidraContainer):
    def __init__(self, *args, custom_validation_callables: list[typing.Callable] | None = None, **kwargs):
        self.custom_validation_callables = (
            custom_validation_callables if custom_validation_callables.__class__ is list else []
        )
        super().__init__(*args, **kwargs)

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

    @validates_schema(pass_original=True)
    def validate_must_use_dynamic_fields(self, _, original_data):
        for custom_validation_callable in self.custom_validation_callables:
            custom_validation_callable(original_data)

    @validates('bf_note')
    def must_have_an_english_and_german_abstract(self, field_data: list[dict]):
        abstracts = self._filter_type_label_schemas(field_data, type_='bf:Summary')
        languages = self._extract_languages_from_type_label_schemas(abstracts)
        errors = []
        if 'eng' not in languages:
            errors.append(MISSING_ENGLISH_ABSTRACT)
        if 'deu' not in languages:
            errors.append(MISSING_GERMAN_ABSTRACT)
        if errors:
            raise ValidationError(errors)

    def _filter_type_label_schemas(self, type_label_schemas: list[dict], type_: str) -> list[dict]:
        return [
            type_label_schema
            for type_label_schema in type_label_schemas
            if ('type' in type_label_schema) and (type_label_schema['type'] == type_)
        ]

    def _extract_languages_from_type_label_schemas(self, type_label_schemas: list[dict]) -> set:
        return {
            label['language']
            for type_label_schema in type_label_schemas
            for label in type_label_schema['skos_prefLabel']
        }


def _str_to_attribute(string: str) -> str:
    return string.replace(':', '_')


def _create_dynamic_phaidra_meta_data_schema(
    bidirectional_concepts_mapper: BidirectionalConceptsMapper,
) -> PhaidraMetaData:
    schema = PhaidraThesisContainer()
    for concept_mapper in bidirectional_concepts_mapper.concept_mappings.values():
        for os_sameAs in concept_mapper.owl_sameAs:
            phaidra_role_code = extract_phaidra_role_code(os_sameAs)
            schema_attribute = _str_to_attribute(phaidra_role_code)
            marshmallow_fields: dict[str, FieldABC] = schema.fields
            """Do not overwrite static field definitions."""
            if schema_attribute not in marshmallow_fields:
                # If there is a field in default/must use roles for validation get it
                if concept_mapper.uri in must_use.DEFAULT_DYNAMIC_ROLES:
                    schema.custom_validation_callables.append(
                        NotFalsyValidator(
                            key=phaidra_role_code,
                            message=must_use.DEFAULT_DYNAMIC_ROLES[concept_mapper.uri].missing_message,
                        )
                    )

                field = PortfolioNestedField(
                    PersonSchema, many=True, required=False, load_from=phaidra_role_code, dump_to=phaidra_role_code
                )
                marshmallow_fields[schema_attribute] = field
    return schema


class ThesisJsonLd(Schema):
    # it is important, that the nested schema is initialized here
    # if not fields will not be available and dynamic fields will not be added (nested)
    json_ld = fields.Nested(
        PhaidraThesisContainer(), many=False, required=True, load_from='json-ld', dump_to='json-ld'
    )


class PhaidraThesisMetaData(Schema):
    # it is important, that the nested schema is initialized here
    # if not fields will not be available and dynamic fields will not be added (nested)
    metadata = fields.Nested(ThesisJsonLd(), many=False, required=True)


def _wrap_dynamic_schema(dynamic_schema: PhaidraContainer) -> PhaidraThesisMetaData:
    schema = PhaidraThesisMetaData()
    schema.fields['metadata'].nested.fields['json_ld'].nested = dynamic_schema
    return schema


def create_dynamic_phaidra_thesis_meta_data_schema(
    bidirectional_concepts_mapper: BidirectionalConceptsMapper,
) -> PhaidraThesisMetaData:
    dynamic_schema = _create_dynamic_phaidra_meta_data_schema(bidirectional_concepts_mapper)
    full_schema = _wrap_dynamic_schema(dynamic_schema)

    return full_schema
