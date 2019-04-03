from datetime import datetime

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from marshmallow import Schema, ValidationError, fields, validate

from ..skosmos import get_preflabel_lazy, get_uri, get_languages


# validators

def validate_date(data):
    try:
        datetime.strptime(data, '%d.%m.%Y')
    except ValueError:
        try:
            datetime.strptime(data, '%Y')
        except ValueError:
            raise ValidationError(_('Invalid date entry (expected dd.mm.yyyy or yyyy)'))


def validate_full_date(data):
    try:
        datetime.strptime(data, '%d.%m.%Y')
    except ValueError:
        raise ValidationError(_('Invalid date entry (expected dd.mm.yyyy)'))


def validate_year(data):
    try:
        datetime.strptime(data, '%Y')
    except ValueError:
        raise ValidationError(_('Invalid date entry (expected yyyy)'))


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


def get_date_field(additional_attributes={}, validator=validate_date):
    return fields.Date(
        title=get_preflabel_lazy('date'),
        additionalProperties=False,
        validate=validator,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'date',
            **additional_attributes
        }},
    )


def get_date_location_group_field(additional_attributes={}):
    return fields.List(
        fields.Nested(DateLocationSchema, additionalProperties=False),
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
            **additional_attributes
        }}
    )


def get_date_range_field(additional_attributes={}):
    return fields.Nested(
        DateRangeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'date',
            **additional_attributes
        }},
    )


def get_date_range_time_range_field(additional_attributes={}):
    return fields.Nested(
        DateRangeTimeRangeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            **additional_attributes
        }},
    )


def get_date_range_time_range_location_group_field(additional_attributes={}):
    return fields.List(
        fields.Nested(DateRangeTimeRangeLocationSchema, additionalProperties=False),
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
            **additional_attributes
        }},
    )


def get_date_time_field(additional_attributes={}):
    return fields.Nested(
        DateTimeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            **additional_attributes
        }},
    )


def get_date_time_range_field(additional_attributes={}):
    return fields.Nested(
        DateTimeRangeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            **additional_attributes
        }},
    )


def get_date_time_range_location_group_field(additional_attributes={}):
    return fields.List(
        fields.Nested(DateTimeRangeLocationSchema, additionalProperties=False),
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
            **additional_attributes
        }},
    )


def get_dimensions_field(additional_attributes={}):
    fields.Str(
        title=get_preflabel_lazy('dimensions'),
        **{'x-attrs': {
            'field_format': 'half',
            **additional_attributes
        }}
    )


def get_duration_field(additional_attributes={}):
    return fields.Str(
        title=get_preflabel_lazy('duration'),
        **{'x-attrs': {
            'field_format': 'half',
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


def get_language_field(additional_attributes={}, required=False):
    return fields.Str(
        validate=validate.OneOf(
            get_languages()[0],
            labels=get_languages()[1],
        ),
        required=required,
        title=get_preflabel_lazy('language'),
        **{'x-attrs': {
            **additional_attributes
        }},
    )


def get_language_list_field(additional_attributes={}):
    return fields.List(
        get_language_field(),
        title=get_preflabel_lazy('language'),
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'languages'}),
            **additional_attributes
        }},
    )


def get_location_field(additional_attributes={}):
    return fields.List(
        fields.Nested(GEOReferenceSchema, additionalProperties=False),
        title=get_preflabel_lazy('location'),
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
            **additional_attributes
        }},
    )


def get_location_description_field(additional_attributes={}):
    return fields.String(
        title=get_preflabel_lazy('location_description'),
        **{'x-attrs': {
            'field_type': 'text',
            **additional_attributes
        }},
    )


def get_location_group_field(additional_attributes={}):
    return fields.List(
        fields.Nested(LocationSchema, additionalProperties=False),
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
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


def get_published_in_field(additional_attributes={}):
    return fields.Str(
        title=get_preflabel_lazy('published_in'),
        **{'x-attrs': {
            'field_type': 'autocomplete',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
            **additional_attributes
        }},
    )


def get_url_field(additional_attributes={}):
    return fields.Url(
        title=get_preflabel_lazy('url'),
        **{'x-attrs': {
            **additional_attributes
        }},
    )


# shared schema definitions

class GEOReferenceSchema(Schema):
    source = fields.Str()
    name = fields.Str()
    latitude = fields.Str()
    longitude = fields.Str()


class DateRangeSchema(Schema):
    date_from = fields.Date(validate=validate_full_date)
    date_to = fields.Date(validate=validate_full_date)


class DateRangeTimeRangeSchema(Schema):
    date_from = fields.Date(validate=validate_full_date)
    date_to = fields.Date(validate=validate_full_date)
    time_from = fields.Time()
    time_to = fields.Time()


class DateTimeSchema(Schema):
    date = fields.Date(validate=validate_full_date)
    time = fields.Time()


class DateTimeRangeSchema(Schema):
    date = fields.Date(validate=validate_full_date)
    time_from = fields.Time()
    time_to = fields.Time()


class LocationSchema(Schema):
    location = get_location_field({'order': 1})
    location_description = get_location_description_field({'field_format': 'half', 'order': 2})


class DateLocationSchema(Schema):
    date = get_date_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'order': 3})


class DateRangeLocationSchema(Schema):
    date = get_date_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})


class DateRangeTimeRangeLocationSchema(Schema):
    date = get_date_range_time_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})


class DateTimeRangeLocationSchema(Schema):
    date = get_date_time_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})


class ContributorSchema(Schema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    name = fields.Str()
    roles = fields.List(fields.Str())


# schema definitions for entry model

# keywords
class KeywordSchema(Schema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    keyword = fields.Str()


class KeywordsModelSchema(Schema):
    keywords = fields.List(fields.Nested(KeywordSchema, additionalProperties=False))


# texts
class TextDataSchema(Schema):
    language = get_language_field(required=True)
    text = fields.Str(required=True, title=get_preflabel_lazy('text'))


class TextSchema(Schema):
    type = fields.Str(title=get_preflabel_lazy('type'))
    data = fields.List(fields.Nested(TextDataSchema, additionalProperties=False))


class TextsModelSchema(Schema):
    texts = fields.List(fields.Nested(TextSchema, additionalProperties=False))
