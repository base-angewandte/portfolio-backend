from marshmallow import Schema

from media_server.archiver.implementations.phaidra.utillities.fields import (
    PortfolioListField,
    PortfolioNestedField,
    PortfolioStringField,
)
from media_server.archiver.implementations.phaidra.utillities.validate import ValidateLength1


class PhaidraJsonLD(Schema):
    ebucore_hasMimeType = PortfolioListField(
        PortfolioStringField(),
        required=True,
        load_from='ebucore:hasMimeType',
        dump_to='ebucore:hasMimeType',
        validate=ValidateLength1(),
    )
    ebucore_filename = PortfolioListField(
        PortfolioStringField(),
        required=True,
        load_from='ebucore:filename',
        dump_to='ebucore:filename',
        validate=ValidateLength1(),
    )
    edm_rights = PortfolioListField(
        PortfolioStringField(), required=True, load_from='edm:rights', dump_to='edm:rights', validate=ValidateLength1()
    )


class PhaidraMetaData(Schema):
    jsonld = PortfolioNestedField(PhaidraJsonLD, many=False, required=True, load_from='json-ld', dump_to='json-ld')


class PhaidraMediaData(Schema):
    """This will be added as json string in files …"""

    metadata = PortfolioNestedField(PhaidraMetaData, many=False, required=True)
