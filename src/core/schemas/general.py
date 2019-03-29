from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from marshmallow import Schema, fields, validate

from ..skosmos import get_preflabel_lazy, get_uri


# contains shared schema definitions
class GEOReferenceSchema(Schema):
    source = fields.Str()
    name = fields.Str()
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
        'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
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
        'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
        'field_format': 'half',

    }})
    location_description = fields.String(**{'x-attrs': {'order': 3, 'field_type': 'text'}})


class DateRangeLocationSchema(Schema):
    date = fields.Nested(DateRangeSchema, additionalProperties=False,
                         title=get_preflabel_lazy('date'),
                         **{'x-attrs': {
                                'order': 1,
                                'field_type': 'date',
                            }})
    location = fields.List(fields.Nested(GEOReferenceSchema, additionalProperties=False),
                           title=get_preflabel_lazy('location'),
                           **{'x-attrs': {
                            'order': 2,
                            'field_type': 'chips',
                            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
                            'field_format': 'half',
                            }})
    location_description = fields.String(
        title=get_preflabel_lazy('location_description'),
        **{'x-attrs': {'order': 3, 'field_type': 'text', 'field_format': 'half'}})


class ContributorSchema(Schema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    name = fields.Str()
    roles = fields.List(fields.Str())


# shared fields

def get_contributors_field(additional_attributes={}):
    return fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy('contributor'),
        **{'x-attrs': {
            'field_type': 'chips-below',
            'placeholder': _('Wähle beteiligte Personen oder Institutionen aus'),
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
            **additional_attributes
        }}
    )


def get_contributors_field_for_role(role, additional_attributes={}):
    return fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy(role),
        **{'x-attrs': {
            'default_role': get_uri(role),
            'equivalent': 'contributors',
            'field_type': 'chips',
            'placeholder': '{} {}'.format(_('Wähle'), get_preflabel_lazy(role)),
            'sortable': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
            **additional_attributes
        }}
    )


def get_format_field(additional_attributes={}):
    return fields.List(
        fields.Str(),
        title=get_preflabel_lazy('format'),
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'sortable': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'formats'}),
            **additional_attributes
        }},
    )


def get_material_field(additional_attributes={}):
    return fields.List(
        fields.Str(),
        title=get_preflabel_lazy('material'),
        **{'x-attrs': {
            'field_type': 'chips',
            'sortable': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'materials'}),
            **additional_attributes
        }},
    )


# schema definitions for entry model

# keywords
class KeywordSchema(Schema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    keyword = fields.Str()


class KeywordsModelSchema(Schema):
    keywords = fields.List(fields.Nested(KeywordSchema, additionalProperties=False))


# texts
class TextDataSchema(Schema):
    language = fields.Str(
        validate=validate.OneOf(
            settings.LANGUAGES_DICT.keys(),
            labels=settings.LANGUAGES_DICT.values(),
        ),
        required=True,
        title=get_preflabel_lazy('language'),
    )
    text = fields.Str(required=True, title=get_preflabel_lazy('text'))


class TextSchema(Schema):
    type = fields.Str(title=get_preflabel_lazy('type'))
    data = fields.List(fields.Nested(TextDataSchema, additionalProperties=False))


class TextsModelSchema(Schema):
    texts = fields.List(fields.Nested(TextSchema, additionalProperties=False))
