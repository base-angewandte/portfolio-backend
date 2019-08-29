from marshmallow import fields, validate

from django.urls import reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import get_language, ugettext_lazy as _

from ..skosmos import get_altlabel_lazy, get_languages_choices, get_preflabel_lazy, get_uri
from ..utils import placeholder_lazy
from .base import BaseSchema, GenericModel

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


def get_contributors_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
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


def get_contributors_field_for_role(role, additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
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


def get_date_field(additional_attributes=None, pattern=r'^\d{4}(-(0[1-9]|1[0-2]))?(-(0[1-9]|[12]\d|3[01]))?$'):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('date')
    return fields.Str(
        title=label,
        additionalProperties=False,
        pattern=pattern,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'date',
            'date_format': 'date_year',
            'placeholder': {'date': placeholder_lazy(label)},
            **additional_attributes
        }},
    )


def get_date_location_group_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = format_lazy(
        '{date} {conjunction} {location}',
        date=get_preflabel_lazy('date'),
        conjunction=_('and'),
        location=get_preflabel_lazy('location'),
    )
    return fields.List(
        fields.Nested(DateLocationSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
            **additional_attributes
        }}
    )


def get_date_range_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('date')
    return fields.Nested(
        DateRangeSchema,
        title=label,
        additionalProperties=False,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'date',
            'date_format': 'day',
            'placeholder': {'date': placeholder_lazy(label)},
            **additional_attributes
        }},
    )


def get_date_range_time_range_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    label = format_lazy(
        '{date} {conjunction} {time}',
        date=label_date,
        conjunction=_('and'),
        time=label_time,
    )
    return fields.Nested(
        DateRangeTimeRangeSchema,
        title=label,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            'date_format': 'day',
            'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
            **additional_attributes
        }},
    )


def get_date_range_time_range_location_group_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = format_lazy(
        '{date}, {time} {conjunction} {location}',
        date=get_preflabel_lazy('date'),
        time=get_preflabel_lazy('time'),
        conjunction=_('and'),
        location=get_preflabel_lazy('location'),
    )
    return fields.List(
        fields.Nested(DateRangeTimeRangeLocationSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
            **additional_attributes
        }},
    )


def get_date_time_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    label = format_lazy(
        '{date} {conjunction} {time}',
        date=label_date,
        conjunction=_('and'),
        time=label_time,
    )
    return fields.Nested(
        DateTimeSchema,
        title=label,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
            **additional_attributes
        }},
    )


def get_date_time_range_field(additional_attributes=None, label=None):
    if additional_attributes is None:
        additional_attributes = {}
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    if label is None:
        label = format_lazy(
            '{date} {conjunction} {time}',
            date=label_date,
            conjunction=_('and'),
            time=label_time,
        )
    return fields.Nested(
        DateTimeRangeSchema,
        title=label,
        additionalProperties=False,
        **{'x-attrs': {
            'field_type': 'date',
            'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
            **additional_attributes
        }},
    )


def get_date_time_range_location_group_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = format_lazy(
        '{date}, {time} {conjunction} {location}',
        date=get_preflabel_lazy('date'),
        time=get_preflabel_lazy('time'),
        conjunction=_('and'),
        location=get_preflabel_lazy('location'),
    )
    return fields.List(
        fields.Nested(DateTimeRangeLocationSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
            **additional_attributes
        }},
    )


def get_dimensions_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_string_field(
        get_preflabel_lazy('dimensions'),
        {
            'field_format': 'half',
            **additional_attributes
        }
    )


def get_duration_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_string_field(
        get_preflabel_lazy('duration'),
        {
            'field_format': 'half',
            **additional_attributes
        }
    )


def get_format_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
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


def get_language_list_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
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


def get_location_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
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


def get_location_description_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_string_field(
        get_preflabel_lazy('location_description'),
        {
            'field_type': 'text',
            **additional_attributes
        }
    )


def get_location_group_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('location')
    return fields.List(
        fields.Nested(LocationSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': False,
            **additional_attributes
        }},
    )


def get_material_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
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


def get_published_in_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
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


def get_url_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_field(
        fields.Str,  # TODO change back to fields.Url
        get_preflabel_lazy('url'),
        {**additional_attributes}
    )


# shared schema definitions

class MultilingualStringSchema(BaseSchema):
    de = fields.Str()
    en = fields.Str()
    fr = fields.Str()


class SourceMultilingualLabelSchema(BaseSchema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    label = fields.Nested(MultilingualStringSchema, additionalProperties=False)


class LanguageDataSchema(BaseSchema):
    source = fields.Str(
        validate=validate.OneOf(
            get_languages_choices()[0],
            labels=get_languages_choices()[1],
        ),
        **{'x-attrs': {'hidden': True}}
    )
    label = fields.Nested(MultilingualStringSchema, additionalProperties=False)


class GEOReferenceModel(GenericModel):
    def to_display_dict(self):
        if self.label:
            return self.label


class GeometrySchema(BaseSchema):
    type = fields.Str()
    coordinates = fields.List(fields.Float())


class GEOReferenceSchema(BaseSchema):
    source = fields.Str()
    label = fields.Str()
    house_number = fields.Str()
    street = fields.Str()
    postcode = fields.Str()
    locality = fields.Str()  # towns, hamlets, cities
    region = fields.Str()
    country = fields.Str()
    geometry = fields.Nested(GeometrySchema, additionalProperties=False)

    __model__ = GEOReferenceModel


class DateRangeModel(GenericModel):
    def to_display_dict(self):
        if self.date_from or self.date_to:
            return {
                'label': get_preflabel_lazy('date'),
                'value': {
                    'from': self.date_from,
                    'to': self.date_to,
                }
            }


class DateRangeSchema(BaseSchema):
    date_from = fields.Date()
    date_to = fields.Date()

    __model__ = DateRangeModel


class DateRangeTimeRangeModel(GenericModel):
    def to_display_dict(self):
        ret = []
        if self.date_from or self.date_to:
            ret.append({
                'label': get_preflabel_lazy('date'),
                'value': {
                    'from': self.date_from,
                    'to': self.date_to,
                }
            })
        if self.time_from or self.time_to:
            ret.append({
                'label': get_preflabel_lazy('time'),
                'value': {
                    'from': self.time_from,
                    'to': self.time_to,
                }
            })
        return ret or None


class DateRangeTimeRangeSchema(BaseSchema):
    date_from = fields.Date()
    date_to = fields.Date()
    time_from = fields.Time(title=get_preflabel_lazy('time'))
    time_to = fields.Time(title=get_preflabel_lazy('time'))

    __model__ = DateRangeTimeRangeModel


class DateTimeSchema(BaseSchema):
    date = fields.Date(title=get_preflabel_lazy('date'))
    time = fields.Time(title=get_preflabel_lazy('time'))


class DateTimeRangeModel(GenericModel):
    def to_display_dict(self):
        ret = []
        if self.date:
            ret.append({
                'label': get_preflabel_lazy('date'),
                'value': self.date
            })
        if self.time_from or self.time_to:
            ret.append({
                'label': get_preflabel_lazy('time'),
                'value': {
                    'from': self.time_from,
                    'to': self.time_to,
                }
            })
        return ret or None


class DateTimeRangeSchema(BaseSchema):
    date = fields.Date(title=get_preflabel_lazy('date'))
    time_from = fields.Time(title=get_preflabel_lazy('time'))
    time_to = fields.Time(title=get_preflabel_lazy('time'))

    __model__ = DateTimeRangeModel


class LocationSchema(BaseSchema):
    location = get_location_field({'order': 1})
    location_description = get_location_description_field({'field_format': 'half', 'order': 2})


class DateLocationSchema(BaseSchema):
    date = get_date_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'order': 3})


class DateRangeLocationSchema(BaseSchema):
    date = get_date_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})


class DateRangeTimeRangeLocationSchema(BaseSchema):
    date = get_date_range_time_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})


class DateTimeRangeLocationSchema(BaseSchema):
    date = get_date_time_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})


class ContributorModel(GenericModel):
    def to_display_dict(self, roles=False):
        if self.label:
            if roles:
                lang = get_language()
                return {
                    'label': self.label,
                    'value': [
                        getattr(x.label, lang) for x in self.roles
                    ] if self.roles else None
                }
            return self.label


class ContributorSchema(BaseSchema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    label = fields.Str()
    roles = fields.List(fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False))

    __model__ = ContributorModel
