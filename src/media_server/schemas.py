from marshmallow import fields

from core.schemas import schema2jsonschema
from core.schemas.base import BaseSchema
from core.schemas.general import SourceMultilingualLabelSchema


# license
class LicenseModelSchema(BaseSchema):
    license = fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False)


def get_license_jsonschema():
    return schema2jsonschema(LicenseModelSchema, force_text=True)['properties']['license']
