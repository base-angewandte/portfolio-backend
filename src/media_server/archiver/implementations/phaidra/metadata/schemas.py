from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from marshmallow.base import FieldABC
    from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import (
        BidirectionalConceptsMapper,
    )

from marshmallow import Schema, fields, validate

from media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping import get_phaidra_role_code

value_field = fields.String(required=True, load_from='@value', dump_to='@value')


class ValueType(Schema):
    value = value_field
    type = fields.Constant('ids:uri', required=True, load_from='@type', dump_to='@type')


class SchemaName(Schema):
    value = value_field


class Person(Schema):
    type = fields.Constant('ids:uri', required=True, load_from='@type', dump_to='@type')
    skos_exactMatch = fields.Nested(
        ValueType(),
        many=True,
        required=True,
        dump_to='skos:exactMatch',
        load_from='skos:exactMatch',
        validate=validate.Length(equal=1),
    )
    schemaName = fields.Nested(
        SchemaName(),
        many=True,
        required=True,
        load_from='schema:name',
        dump_to='schema:name',
        validate=validate.Length(equal=1),
    )


class SkosPrefLabel(Schema):
    value = value_field
    language = fields.String(required=True, load_from='@language', dump_to='@language')


class TypeLabel(Schema):
    type = fields.Constant('skos:Concept', required=True, load_from='@type', dump_to='@type')
    skos_prefLabel = fields.Nested(
        SkosPrefLabel(), many=True, required=True, load_from='skos:prefLabel', dump_to='skos:prefLabel'
    )


class TypeLabelMatchSchema(TypeLabel):
    skos_exactMatch = fields.List(fields.String(), required=True, validate=validate.Length(equal=1))


class TitleType(Schema):
    """bf:mainTitle and @bf:subtitle."""

    value = fields.String(required=True, load_from='@value', dump_to='@value')
    language = fields.Constant('und', required=True, load_from='@language', dump_to='@language')


class DceTitle(Schema):
    type = fields.Constant('bf:Title', required=True, load_from='@type', dump_to='@type')
    bf_mainTitle = fields.Nested(TitleType, required=True, load_from='bf:mainTitle', dump_to='bf:mainTitle')
    bf_subtitle = fields.Nested(TitleType, required=True, load_from='bf:subtitle', dump_to='bf:subtitle')


class _PhaidraMetaData(Schema):
    dcterms_type = fields.Constant(
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

    edm_hasType = fields.Nested(TypeLabel(), many=True, load_from='edm:hasType', dump_to='edm:hasType', required=True)

    dce_title = fields.Nested(
        DceTitle(),
        many=True,
        required=True,
        validate=validate.Length(equal=1),
        load_from='dce:title',
        dump_to='dce:title',
    )

    dcterms_subject = fields.Nested(
        TypeLabelMatchSchema(), many=True, required=True, load_from='dcterms:subject', dump_to='dcterms:subject'
    )

    rdau_P60048 = fields.Nested(
        TypeLabelMatchSchema(), many=True, required=True, load_from='rdau:P60048', dump_to='rdau:P60048'
    )

    dce_format = fields.Nested(
        TypeLabelMatchSchema(), many=True, required=True, load_from='dce:format', dump_to='dce:format'
    )

    bf_note = fields.Nested(TypeLabelMatchSchema(), many=True, required=True, load_from='bf:note', dump_to='bf:note')

    role_edt = fields.Nested(Person(), many=True, required=True, load_from='role:edt', dump_to='role:edt')

    role_aut = fields.Nested(Person(), many=True, required=True, load_from='role:aut', dump_to='role:aut')

    role_pbl = fields.Nested(Person(), many=True, required=True, load_from='role:pbl', dump_to='role:pbl')


def _str_to_attribute(string: str) -> str:
    return string.replace(':', '_')


def get_phaidra_meta_data_schema_with_dynamic_fields(
    bidirectional_concepts_mapper: 'BidirectionalConceptsMapper',
) -> _PhaidraMetaData:
    schema = _PhaidraMetaData()
    for concept_mapper in bidirectional_concepts_mapper.concept_mappings.values():
        for os_sameAs in concept_mapper.owl_sameAs:
            phaidra_role_code = get_phaidra_role_code(os_sameAs)
            schema_attribute = _str_to_attribute(phaidra_role_code)
            marshmallow_fields: Dict[str, 'FieldABC'] = schema.fields
            '''Do not overwrite static field definitions'''
            if schema_attribute not in marshmallow_fields:
                marshmallow_fields[schema_attribute] = fields.Nested(
                    Person(), many=True, required=False, load_from=phaidra_role_code, dump_to=phaidra_role_code
                )
    schema
