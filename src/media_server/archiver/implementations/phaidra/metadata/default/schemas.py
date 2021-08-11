"""Check out src/media_server/archiver/implementations/phaidra/phaidra_tests/te
st_media_metadata.py Check out src/media_server/archiver/implementations/phaidr
a/metadata/datatranslation.py."""

from marshmallow import Schema, fields

from media_server.archiver.implementations.phaidra.utillities.fields import (
    PortfolioConstantField,
    PortfolioListField,
    PortfolioNestedField,
    PortfolioStringField,
)
from media_server.archiver.implementations.phaidra.utillities.validate import ValidateLength1

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
    type = PortfolioConstantField('schema:Person', load_from='@type', dump_to='@type')
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


class PhaidraContainer(Schema):
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
        SkosConceptSchema, many=True, load_from='dcterms:language', dump_to='dcterms:language', validate=None
    )

    dcterms_subject = PortfolioNestedField(
        SkosConceptSchema,
        many=True,
        load_from='dcterms:subject',
        dump_to='dcterms:subject',
        validate=None,
    )

    rdau_P60048 = PortfolioNestedField(
        SkosConceptSchema,
        many=True,
        load_from='rdau:P60048',
        dump_to='rdau:P60048',
        validate=None,
    )

    dce_format = PortfolioNestedField(
        SkosConceptSchema,
        many=True,
        load_from='dce:format',
        dump_to='dce:format',
        validate=None,
    )

    bf_note = PortfolioNestedField(
        TypeLabelSchema,
        many=True,
        load_from='bf:note',
        dump_to='bf:note',
        validate=None,
    )

    role_edt = PortfolioNestedField(PersonSchema, many=True, load_from='role:edt', dump_to='role:edt', validate=None)

    role_aut = PortfolioNestedField(PersonSchema, many=True, load_from='role:aut', dump_to='role:aut', validate=None)

    role_pbl = PortfolioNestedField(PersonSchema, many=True, load_from='role:pbl', dump_to='role:pbl', validate=None)


class JsonLd(Schema):
    # it is important, that the nested schema is initialized here
    # if not fields will not be available and dynamic fields will not be added (nested)
    json_ld = fields.Nested(PhaidraContainer(), many=False, required=True, load_from='json-ld', dump_to='json-ld')


class PhaidraMetaData(Schema):
    # it is important, that the nested schema is initialized here
    # if not fields will not be available and dynamic fields will not be added (nested)
    metadata = fields.Nested(JsonLd(), many=False, required=True)
