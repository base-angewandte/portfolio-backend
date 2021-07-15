from marshmallow import fields, validate

from media_server.archiver.implementations.phaidra.metadata.default.schemas import PersonSchema, _PhaidraMetaData


class _PhaidraThesisMetaDataSchema(_PhaidraMetaData):

    role_aut = fields.Nested(
        PersonSchema, many=True, validate=validate.Length(min=1), load_from='role:aut', dump_to='role:aut'
    )
