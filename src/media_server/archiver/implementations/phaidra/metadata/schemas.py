from marshmallow import Schema, fields, validate


class SkosPrefLabel(Schema):
    value = fields.String(required=True, load_from='@value', dump_to='@value')
    language = fields.String(required=True, load_from='@language', dump_to='@language')


class TypeLabel(Schema):
    type = fields.Constant('skos:Concept', required=True, load_from='@type', dump_to='@type')
    skos_prefLabel = fields.List(SkosPrefLabel(), required=True, load_from='skos:prefLabel', dump_to='skos:prefLabel')


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


class PhaidraMetaData(Schema):
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

    edm_hasType = fields.List(TypeLabel(), load_from='edm:hasType', dump_to='edm:hasType', required=True)

    dce_title = fields.List(
        DceTitle(),
        required=True,
        validate=validate.Length(equal=1),
        load_from='dce:title',
        dump_to='dce:title',
    )

    dcterms_subject = fields.List(
        TypeLabelMatchSchema(), required=True, load_from='dcterms:subject', dump_to='dcterms:subject'
    )

    rdau_P60048 = fields.List(TypeLabelMatchSchema(), required=True, load_from='rdau:P60048', dump_to='rdau:P60048')

    dce_format = fields.List(TypeLabelMatchSchema(), required=True, load_from='dce:format', dump_to='dce:format')

    bf_note = fields.List(TypeLabelMatchSchema(), required=True, load_from='bf:note', dump_to='bf:note')
