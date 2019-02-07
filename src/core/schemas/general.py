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


class DateSchema(Schema):
    date = fields.Date()


class DateRangeSchema(Schema):
    date_from = fields.Date()
    date_to = fields.Date()


class DateTimeSchema(Schema):
    date = fields.Date()
    time = fields.Time()


class LocationSchema(Schema):
    location = fields.List(fields.Nested(GEOReferenceSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/place/',
        'field_format': 'half',
    }})
    location_description = fields.String(**{'x-attrs': {'order': 3, 'field_type': 'text', 'field_format': 'half'}})


# TODO: currently only used for architecture (and not sure it is needed there) - check if this is necessary
class DateLocationSchema(Schema):
    date = fields.Nested(DateSchema, additionalProperties=False, **{'x-attrs': {
        'order': 1,
        'field_type': 'date',
        'field_format': 'half',
    }})
    location = fields.List(fields.Nested(GEOReferenceSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/place/',
        'field_format': 'half',

    }})
    location_description = fields.String(**{'x-attrs': {'order': 3, 'field_type': 'text'}})


class DateRangeLocationSchema(Schema):
    date = fields.Nested(DateRangeSchema, additionalProperties=False, **{'x-attrs': {
        'order': 1,
        'field_type': 'date',
    }})
    location = fields.List(fields.Nested(GEOReferenceSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/place/',
        'field_format': 'half',

    }})
    location_description = fields.String(**{'x-attrs': {'order': 3, 'field_type': 'text', 'field_format': 'half'}})


class ContributorSchema(Schema):
    source_id = fields.Str()
    commonname = fields.Str()
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    role = fields.Str()


# Text
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
    data = fields.List(fields.Nested(TextDataSchema, additionalProperties=False))


class TextModelSchema(Schema):
    text = fields.List(fields.Nested(TextSchema, additionalProperties=False))
