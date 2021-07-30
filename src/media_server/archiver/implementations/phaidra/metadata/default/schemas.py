"""Check out src/media_server/archiver/implementations/phaidra/phaidra_tests/te
st_media_metadata.py Check out src/media_server/archiver/implementations/phaidr
a/metadata/datatranslation.py."""
from typing import TYPE_CHECKING, Dict, Type

from marshmallow import Schema, fields

from media_server.archiver.implementations.phaidra.utillities.fields import (
    PortfolioConstantField,
    PortfolioListField,
    PortfolioNestedField,
    PortfolioStringField,
)
from media_server.archiver.implementations.phaidra.utillities.validate import ValidateLength1

if TYPE_CHECKING:
    from marshmallow.base import FieldABC
    from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
        BidirectionalConceptsMapper,
    )

from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
    extract_phaidra_role_code,
)

value_field = PortfolioStringField(required=True, load_from='@value', dump_to='@value')


class ValueSchema(Schema):
    value_field = value_field


class ValueTypeBaseSchema(Schema):
    value = value_field
    type = PortfolioConstantField('ids:uri', load_from='@type', dump_to='@type')


class ValueLanguageBaseSchema(Schema):
    value = value_field
    language = PortfolioStringField(required=True, load_from='@language', dump_to='@language')


class TypeLabelSchema(Schema):
    type = PortfolioStringField(required=True, load_from='@type', dump_to='@type')
    skos_prefLabel = PortfolioNestedField(
        ValueLanguageBaseSchema, required=True, many=True, load_from='skos:prefLabel', dump_to='skos:prefLabel'
    )


class SkosConceptSchema(TypeLabelSchema):
    type = PortfolioConstantField('skos:Concept', load_from='@type', dump_to='@type')
    skos_exactMatch = PortfolioListField(
        PortfolioStringField(),
        validate=ValidateLength1(),
        required=True,
        load_from='skos:exactMatch',
        dump_to='skos:exactMatch',
    )


class PersonSchema(Schema):
    type = PortfolioConstantField('ids:uri', load_from='@type', dump_to='@type')
    skos_exactMatch = PortfolioNestedField(
        ValueTypeBaseSchema,
        many=True,
        dump_to='skos:exactMatch',
        load_from='skos:exactMatch',
        required=True,
    )
    schema_Name = PortfolioNestedField(
        ValueSchema,
        many=True,
        load_from='schema:name',
        dump_to='schema:name',
        validate=ValidateLength1(),
        required=True,
    )


class DceTitleSchema(Schema):
    type = PortfolioConstantField('bf:Title', required=True, load_from='@type', dump_to='@type')
    bf_mainTitle = PortfolioNestedField(
        ValueLanguageBaseSchema,
        required=True,
        load_from='bf:mainTitle',
        dump_to='bf:mainTitle',
        many=True,
    )
    bf_subtitle = PortfolioNestedField(
        ValueLanguageBaseSchema, load_from='bf:subtitle', dump_to='bf:subtitle', many=True
    )


class _PhaidraMetaData(Schema):
    dcterms_type = PortfolioConstantField(
        [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
            }
        ],
        dump_to='dcterms:type',
        load_from='dcterms:type',
    )

    edm_hasType = PortfolioNestedField(
        SkosConceptSchema,
        many=True,
        load_from='edm:hasType',
        dump_to='edm:hasType',
    )

    dce_title = PortfolioNestedField(
        DceTitleSchema,
        required=True,
        many=True,
        validate=ValidateLength1(),
        load_from='dce:title',
        dump_to='dce:title',
    )

    dcterms_language = PortfolioNestedField(
        SkosConceptSchema, many=True, load_from='dcterms:language', dump_to='dcterms:language'
    )

    dcterms_subject = PortfolioNestedField(
        SkosConceptSchema, many=True, load_from='dcterms:subject', dump_to='dcterms:subject'
    )

    rdau_P60048 = PortfolioNestedField(SkosConceptSchema, many=True, load_from='rdau:P60048', dump_to='rdau:P60048')

    dce_format = PortfolioNestedField(SkosConceptSchema, many=True, load_from='dce:format', dump_to='dce:format')

    bf_note = PortfolioNestedField(TypeLabelSchema, many=True, load_from='bf:note', dump_to='bf:note')

    role_edt = PortfolioNestedField(PersonSchema, many=True, load_from='role:edt', dump_to='role:edt')

    role_aut = PortfolioNestedField(PersonSchema, many=True, load_from='role:aut', dump_to='role:aut')

    role_pbl = PortfolioNestedField(PersonSchema, many=True, load_from='role:pbl', dump_to='role:pbl')


class Container(Schema):
    # _PhaidraMetaData is actually a placeholder.
    # it will be replaced with _PhaidraMetaData() or ChildClassOf_PhaidraMetaData()
    container = fields.Nested(_PhaidraMetaData, many=False, required=True)


class JsonLd(Schema):
    # it is important, that the nested schema is initialized here
    # if not fields will not be available and dynamic fields will not be added (nested)
    json_ld = fields.Nested(Container(), many=False, required=True, load_from='json-ld', dump_to='json-ld')


class PhaidraMetaData(Schema):
    # it is important, that the nested schema is initialized here
    # if not fields will not be available and dynamic fields will not be added (nested)
    metadata = fields.Nested(JsonLd(), many=False, required=True)


def _str_to_attribute(string: str) -> str:
    return string.replace(':', '_')


def _create_dynamic_phaidra_meta_data_schema(
    bidirectional_concepts_mapper: 'BidirectionalConceptsMapper',
    base_schema_class: Type[_PhaidraMetaData] = _PhaidraMetaData,
) -> PhaidraMetaData:
    schema = base_schema_class()
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


def _wrap_dynamic_schema(dynamic_schema: _PhaidraMetaData) -> PhaidraMetaData:
    schema = PhaidraMetaData()
    schema.fields['metadata'].nested.fields['json_ld'].nested.fields['container'].nested = dynamic_schema
    return schema


def create_dynamic_phaidra_meta_data_schema(
    bidirectional_concepts_mapper: 'BidirectionalConceptsMapper',
    base_schema_class: Type[_PhaidraMetaData] = _PhaidraMetaData,
) -> PhaidraMetaData:
    dynamic_schema = _create_dynamic_phaidra_meta_data_schema(bidirectional_concepts_mapper, base_schema_class)
    full_schema = _wrap_dynamic_schema(dynamic_schema)
    return full_schema
