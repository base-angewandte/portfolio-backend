from datetime import datetime

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from marshmallow import Schema, ValidationError, fields, validate

from ..skosmos import get_preflabel_lazy, get_uri, get_languages_choices, get_altlabel_lazy
from ..utils import placeholder_lazy


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

def get_field(field, label, additional_attributes):
    return field(
        title=label,
        **{'x-attrs': {
            'placeholder': placeholder_lazy(label),
            **additional_attributes
        }},
    )


def get_string_field(label, additional_attributes):
    return get_field(fields.Str, label, additional_attributes)


def get_contributors_field(additional_attributes={}):
    label = get_altlabel_lazy('contributor')
    return fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_type': 'chips-below',
            'placeholder': placeholder_lazy(label),
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
            'source_role': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'roles'}),
            'prefetch': ['source_role'],
            'allow_unkown_entries': True,
            'dynamic_autosuggest': True,
            **additional_attributes
        }}
    )


def get_contributors_field_for_role(role, additional_attributes={}):
    label = get_altlabel_lazy(role)
    return fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'default_role': get_uri(role),
            'equivalent': 'contributors',
            'field_type': 'chips',
            'placeholder': placeholder_lazy(label),
            'sortable': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
            'allow_unkown_entries': True,
            'dynamic_autosuggest': True,
            **additional_attributes
        }}
    )


def get_date_field(additional_attributes={}, validator=validate_date):
    label = get_preflabel_lazy('date')
    return fields.Date(
        title=label,
        additionalProperties=False,
        validate=validator,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'date',
            'date_format': 'date_year',
            'placeholder': {'date': placeholder_lazy(label)},
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
    label = get_preflabel_lazy('date')
    return fields.Nested(
        DateRangeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'date',
            'date_format': 'day',
            'placeholder': {'date': placeholder_lazy(label)},
            **additional_attributes
        }},
    )


def get_date_range_time_range_field(additional_attributes={}):
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    return fields.Nested(
        DateRangeTimeRangeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            'date_format': 'day',
            'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
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
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    return fields.Nested(
        DateTimeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
            **additional_attributes
        }},
    )


def get_date_time_range_field(additional_attributes={}):
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    return fields.Nested(
        DateTimeRangeSchema,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
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
    return get_string_field(
        get_preflabel_lazy('dimensions'),
        {
            'field_format': 'half',
            **additional_attributes
        }
    )


def get_duration_field(additional_attributes={}):
    return get_string_field(
        get_preflabel_lazy('duration'),
        {
            'field_format': 'half',
            **additional_attributes
        }
    )


def get_format_field(additional_attributes={}):
    label = get_preflabel_lazy('format')
    return fields.List(
        fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'sortable': True,
            'allow_unkown_entries': True,
            'set_label_language': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'formats'}),
            'prefetch': ['source'],
            'placeholder': placeholder_lazy(label),
            **additional_attributes
        }},
    )


def get_language_list_field(additional_attributes={}):
    label = get_preflabel_lazy('language')
    return fields.List(
        fields.Nested(LanguageDataSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'set_label_language': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'languages'}),
            'prefetch': ['source'],
            'placeholder': placeholder_lazy(label),
            **additional_attributes
        }},
    )


def get_location_field(additional_attributes={}):
    label = get_preflabel_lazy('location')
    return fields.List(
        fields.Nested(GEOReferenceSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'dynamic_autosuggest': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
            'placeholder': placeholder_lazy(label),
            **additional_attributes
        }},
    )


def get_location_description_field(additional_attributes={}):
    return get_string_field(
        get_preflabel_lazy('location_description'),
        {
            'field_type': 'text',
            **additional_attributes
        }
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
    label = get_preflabel_lazy('material')
    return fields.List(
        fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_type': 'chips',
            'sortable': True,
            'allow_unkown_entries': True,
            'set_label_language': True,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'materials'}),
            'prefetch': ['source'],
            'placeholder': placeholder_lazy(label),
            **additional_attributes
        }},
    )


def get_published_in_field(additional_attributes={}):
    return get_string_field(
        get_preflabel_lazy('published_in'),
        {
            # TODO: changed from autocomplete to text until autocomplete available
            'field_type': 'text',
            'field_format': 'half',
            # 'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
            **additional_attributes
        }
    )


def get_url_field(additional_attributes={}):
    return get_field(
        fields.Str,  # TODO change back to fields.Url
        get_preflabel_lazy('url'),
        {**additional_attributes}
    )


# shared schema definitions

class MultilingualStringSchema(Schema):
    de = fields.Str()
    en = fields.Str()
    fr = fields.Str()


class SourceMultilingualLabelSchema(Schema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    label = fields.Nested(MultilingualStringSchema, additionalProperties=False)


class LanguageDataSchema(Schema):
    source = fields.Str(
        validate=validate.OneOf(
            get_languages_choices()[0],
            labels=get_languages_choices()[1],
        ),
        **{'x-attrs': {'hidden': True}}
    )
    label = fields.Nested(MultilingualStringSchema, additionalProperties=False)


class GeometrySchema(Schema):
    type = fields.Str()
    coordinates = fields.List(fields.Float())


class GEOReferenceSchema(Schema):
    source = fields.Str()
    label = fields.Str()
    house_number = fields.Str()
    street = fields.Str()
    postcode = fields.Str()
    locality = fields.Str()  # towns, hamlets, cities
    region = fields.Str()
    country = fields.Str()
    geometry = fields.Nested(GeometrySchema, additionalProperties=False)


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
    label = fields.Str()
    roles = fields.List(fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False))
