from django.conf import settings
from marshmallow import Schema, fields, validate

from ..skosmos import get_preflabel_lazy


# contains shared schema definitions
class GEOReferenceSchema(Schema):
    geoname_id = fields.Str()
    geoname_name = fields.Str()
    country_name = fields.Str()
    latitude = fields.Str()
    longitude = fields.Str()


class InstitutionSchema(Schema):
    source_id = fields.Str()
    commonname = fields.Str()
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    role = fields.Str()


class PersonSchema(Schema):
    source_id = fields.Str()
    commonname = fields.Str()
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    role = fields.Str()


class TextDataSchema(Schema):
    language = fields.Str(
        validate=validate.OneOf(
            settings.LANGUAGES_DICT.keys(),
            labels=settings.LANGUAGES_DICT.values(),
        ),
        required=True,
        title=get_preflabel_lazy('c_language'),
    )
    text = fields.Str(required=True, title=get_preflabel_lazy('c_text'))


class TextSchema(Schema):
    type = fields.Str(title=get_preflabel_lazy('c_type'))
    data = fields.Nested(TextDataSchema, additionalProperties=False)
