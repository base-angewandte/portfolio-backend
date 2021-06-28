from marshmallow import Schema, fields


class PhaidraJsonLD(Schema):
    ebucore_hasMimeType = fields.List(
        fields.String(), required=True, load_from='ebucore:hasMimeType', dump_to='ebucore:hasMimeType'
    )
    ebucore_filename = fields.List(
        fields.String(), required=True, load_from='ebucore:filename', dump_to='ebucore:filename'
    )
    edm_Rights = fields.List(fields.String(), required=True, load_from='edm:rights', dump_to='edm:rights')


class PhaidraMetaData(Schema):
    jsonld = fields.Nested(PhaidraJsonLD, many=False, required=True, load_from='json-ld', dump_to='json-ld')


class PhaidraMediaData(Schema):
    """This will be added as json string in files …"""

    metadata = fields.Nested(PhaidraMetaData, many=False, required=True)
