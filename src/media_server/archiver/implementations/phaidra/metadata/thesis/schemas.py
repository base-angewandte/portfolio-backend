from typing import TYPE_CHECKING, Dict, List, Set

if TYPE_CHECKING:
    from marshmallow.base import FieldABC

from marshmallow import ValidationError, validates

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
from media_server.archiver.implementations.phaidra.utillities.fields import PortfolioNestedField
from media_server.archiver.implementations.phaidra.utillities.validate import (
    ValidateAuthor,
    ValidateLanguage,
    ValidateSupervisor,
)
from media_server.archiver.messages.validation.thesis import MISSING_ENGLISH_ABSTRACT, MISSING_GERMAN_ABSTRACT


class PhaidraThesisContainer(PhaidraContainer):
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


def _str_to_attribute(string: str) -> str:
    return string.replace(':', '_')


def _create_dynamic_phaidra_meta_data_schema(
    bidirectional_concepts_mapper: 'BidirectionalConceptsMapper',
) -> PhaidraMetaData:
    schema = PhaidraThesisContainer()
    for concept_mapper in bidirectional_concepts_mapper.concept_mappings.values():
        for os_sameAs in concept_mapper.owl_sameAs:
            phaidra_role_code = extract_phaidra_role_code(os_sameAs)
            schema_attribute = _str_to_attribute(phaidra_role_code)
            marshmallow_fields: Dict[str, 'FieldABC'] = schema.fields
            '''Do not overwrite static field definitions'''
            if schema_attribute not in marshmallow_fields:
                marshmallow_fields[schema_attribute] = PortfolioNestedField(
                    PersonSchema, many=True, required=False, load_from=phaidra_role_code, dump_to=phaidra_role_code
                )
    return schema


def _wrap_dynamic_schema(dynamic_schema: PhaidraContainer) -> PhaidraMetaData:
    schema = PhaidraMetaData()
    schema.fields['metadata'].nested.fields['json_ld'].nested.fields['container'].nested = dynamic_schema
    return schema


def create_dynamic_phaidra_meta_data_schema(
    bidirectional_concepts_mapper: 'BidirectionalConceptsMapper',
) -> PhaidraMetaData:
    dynamic_schema = _create_dynamic_phaidra_meta_data_schema(bidirectional_concepts_mapper)
    full_schema = _wrap_dynamic_schema(dynamic_schema)
    return full_schema
