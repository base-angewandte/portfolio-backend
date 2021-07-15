from marshmallow import fields, validate

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
