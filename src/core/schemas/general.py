import logging

from marshmallow import fields, validate

from django.urls import reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import get_language, gettext_lazy as _

from ..skosmos import get_altlabel_lazy, get_languages_choices, get_preflabel, get_preflabel_lazy, get_uri
from ..utils import placeholder_lazy
from .base import BaseSchema, GenericModel

logger = logging.getLogger(__name__)

# shared fields


def get_field(field, label, additional_attributes):
    return field(
        title=label,
        **{'x-attrs': {'placeholder': placeholder_lazy(label), **additional_attributes}},
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
        **{
            'x-attrs': {
                'field_type': 'chips-below',
                'placeholder': placeholder_lazy(label),
                'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
                'source_role': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'roles'}),
                'prefetch': ['source_role'],
                'allow_unknown_entries': True,
                'dynamic_autosuggest': True,
                **additional_attributes,
            }
        },
    )


def get_contributors_field_for_role(role, additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_altlabel_lazy(role)
    return fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=label,
        **{
            'x-attrs': {
                'default_role': get_uri(role),
                'equivalent': 'contributors',
                'field_type': 'chips',
                'placeholder': placeholder_lazy(label),
                'sortable': True,
                'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributors'}),
                'allow_unknown_entries': True,
                'dynamic_autosuggest': True,
                **additional_attributes,
            }
        },
    )


def get_date_field(additional_attributes=None, pattern=r'^\d{4}(-(0[1-9]|1[0-2]))?(-(0[1-9]|[12]\d|3[01]))?$'):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('date')
    return fields.Str(
        title=label,
        additionalProperties=False,
        pattern=pattern,
        **{
            'x-attrs': {
                'field_format': 'half',
                'field_type': 'date',
                'date_format': 'date_year',
                'placeholder': {'date': placeholder_lazy(label)},
                **additional_attributes,
            }
        },
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
        **{'x-attrs': {'field_type': 'group', 'show_label': False, **additional_attributes}},
    )


def get_date_range_location_group_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = format_lazy(
        '{date} {conjunction} {location}',
        date=get_preflabel_lazy('date'),
        conjunction=_('and'),
        location=get_preflabel_lazy('location'),
    )
    return fields.List(
        fields.Nested(DateRangeLocationSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {'field_type': 'group', 'show_label': False, **additional_attributes}},
    )


def get_date_range_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('date')
    return fields.Nested(
        DateRangeSchema,
        title=label,
        additionalProperties=False,
        **{
            'x-attrs': {
                'field_type': 'date',
                'date_format': 'day',
                'placeholder': {'date': placeholder_lazy(label)},
                **additional_attributes,
            }
        },
    )


def get_date_range_time_range_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    label = format_lazy('{date} {conjunction} {time}', date=label_date, conjunction=_('and'), time=label_time)
    return fields.Nested(
        DateRangeTimeRangeSchema,
        title=label,
        additionalProperties=False,
        **{
            'x-attrs': {
                'field_type': 'date',
                'date_format': 'day',
                'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
                **additional_attributes,
            }
        },
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
        **{'x-attrs': {'field_type': 'group', 'show_label': False, **additional_attributes}},
    )


def get_date_time_field(additional_attributes=None, label=None):
    if additional_attributes is None:
        additional_attributes = {}
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    if label is None:
        label = format_lazy('{date} {conjunction} {time}', date=label_date, conjunction=_('and'), time=label_time)
    return fields.Nested(
        DateTimeSchema,
        title=label,
        additionalProperties=False,
        **{
            'x-attrs': {
                'field_type': 'date',
                'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
                **additional_attributes,
            }
        },
    )


def get_date_time_range_field(additional_attributes=None, label=None):
    if additional_attributes is None:
        additional_attributes = {}
    label_date = get_preflabel_lazy('date')
    label_time = get_preflabel_lazy('time')
    if label is None:
        label = format_lazy('{date} {conjunction} {time}', date=label_date, conjunction=_('and'), time=label_time)
    return fields.Nested(
        DateTimeRangeSchema,
        title=label,
        additionalProperties=False,
        **{
            'x-attrs': {
                'field_type': 'date',
                'placeholder': {'date': placeholder_lazy(label_date), 'time': placeholder_lazy(label_time)},
                **additional_attributes,
            }
        },
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
        **{'x-attrs': {'field_type': 'group', 'show_label': False, **additional_attributes}},
    )


def get_dimensions_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_string_field(get_preflabel_lazy('dimensions'), {'field_format': 'half', **additional_attributes})


def get_duration_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_string_field(get_preflabel_lazy('duration'), {'field_format': 'half', **additional_attributes})


def get_format_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('format')
    return fields.List(
        fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False),
        title=label,
        **{
            'x-attrs': {
                'field_format': 'half',
                'field_type': 'chips',
                'sortable': True,
                'allow_unknown_entries': True,
                'set_label_language': True,
                'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'formats'}),
                'prefetch': ['source'],
                'placeholder': placeholder_lazy(label),
                **additional_attributes,
            }
        },
    )


def get_language_list_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('language')
    return fields.List(
        fields.Nested(LanguageDataSchema, additionalProperties=False),
        title=label,
        **{
            'x-attrs': {
                'field_format': 'half',
                'field_type': 'chips',
                'set_label_language': True,
                'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'languages'}),
                'prefetch': ['source'],
                'placeholder': placeholder_lazy(label),
                **additional_attributes,
            }
        },
    )


def get_location_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('location')
    return fields.List(
        fields.Nested(GEOReferenceSchema, additionalProperties=False),
        title=label,
        **{
            'x-attrs': {
                'field_format': 'half',
                'field_type': 'chips',
                'dynamic_autosuggest': True,
                'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'places'}),
                'placeholder': placeholder_lazy(label),
                **additional_attributes,
            }
        },
    )


def get_location_description_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_string_field(
        get_preflabel_lazy('location_description'), {'field_type': 'text', **additional_attributes}
    )


def get_location_group_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('location')
    return fields.List(
        fields.Nested(LocationSchema, additionalProperties=False),
        title=label,
        **{'x-attrs': {'field_type': 'group', 'show_label': False, **additional_attributes}},
    )


def get_material_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('material')
    return fields.List(
        fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False),
        title=label,
        **{
            'x-attrs': {
                'field_type': 'chips',
                'sortable': True,
                'allow_unknown_entries': True,
                'set_label_language': True,
                'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'materials'}),
                'prefetch': ['source'],
                'placeholder': placeholder_lazy(label),
                **additional_attributes,
            }
        },
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
            **additional_attributes,
        },
    )


def get_status_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    label = get_preflabel_lazy('status')
    return fields.Nested(
        SourceMultilingualLabelSchema,
        title=label,
        additionalProperties=False,
        **{
            'x-attrs': {
                'field_format': 'half',
                'field_type': 'chips',
                'set_label_language': True,
                'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'statuses'}),
                'type': 'object',
                'prefetch': ['source'],
                'placeholder': placeholder_lazy(label),
                **additional_attributes,
            }
        },
    )


def get_url_field(additional_attributes=None):
    if additional_attributes is None:
        additional_attributes = {}
    return get_field(
        fields.Str, get_preflabel_lazy('url'), {**additional_attributes}  # TODO change back to fields.Url
    )


# shared schema definitions


class SourceMultilingualLabelModel(GenericModel):
    def to_display(self, roles=False):
        if self.label:
            lang = get_language()
            return getattr(self.label, lang)


class MultilingualStringSchema(BaseSchema):
    de = fields.Str()
    en = fields.Str()
    fr = fields.Str()


class SourceMultilingualLabelSchema(BaseSchema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    label = fields.Nested(MultilingualStringSchema, additionalProperties=False)

    __model__ = SourceMultilingualLabelModel


class LanguageDataSchema(BaseSchema):
    source = fields.Str(
        validate=validate.OneOf(
            get_languages_choices()[0],
            labels=get_languages_choices()[1],
        ),
        **{'x-attrs': {'hidden': True}},
    )
    label = fields.Nested(MultilingualStringSchema, additionalProperties=False)

    __model__ = SourceMultilingualLabelModel


class GEOReferenceModel(GenericModel):
    def to_display(self):
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


class DateTimeLocationModel(GenericModel):
    def _value_dict(self, attribute, label=None, is_range=False):
        if label is None:
            label = self.metadata.get(attribute, {}).get('title')
        if is_range:
            return {'label': label, 'value': {x: getattr(self, f'{attribute}_{x}') for x in ['from', 'to']}}
        else:
            return {
                'label': label,
                'value': getattr(self, attribute),
            }

    def to_display(self):
        ret = []
        if hasattr(self, 'date') and self.date:
            if isinstance(self.date, GenericModel):
                ret += self.date.to_display()
            else:
                ret.append(self._value_dict('date'))
        elif hasattr(self, 'date_from') and (self.date_from or self.date_to):
            ret.append(self._value_dict('date', label=get_preflabel_lazy('date'), is_range=True))
        if hasattr(self, 'time_from') and (self.time_from or self.time_to):
            ret.append(self._value_dict('time', label=get_preflabel_lazy('time'), is_range=True))
        if hasattr(self, 'opening') and self.opening:
            ret.append({'label': self.metadata.get('opening', {}).get('title'), 'value': self.opening.to_display()})
        if hasattr(self, 'location') and self.location:
            ret.append(
                {
                    'label': self.metadata.get('location', {}).get('title'),
                    'value': [x.to_display() for x in self.location],
                }
            )
        if hasattr(self, 'location_description') and self.location_description:
            ret.append(self._value_dict('location_description'))
        return ret


class DateRangeSchema(BaseSchema):
    date_from = fields.Date()
    date_to = fields.Date()

    __model__ = DateTimeLocationModel


class DateRangeTimeRangeSchema(BaseSchema):
    date_from = fields.Date()
    date_to = fields.Date()
    time_from = fields.Time(title=get_preflabel_lazy('time'))
    time_to = fields.Time(title=get_preflabel_lazy('time'))

    __model__ = DateTimeLocationModel


class DateTimeSchema(BaseSchema):
    date = fields.Date(title=get_preflabel_lazy('date'))
    time = fields.Time(title=get_preflabel_lazy('time'))

    __model__ = DateTimeLocationModel


class DateTimeRangeSchema(BaseSchema):
    date = fields.Date(title=get_preflabel_lazy('date'))
    time_from = fields.Time(title=get_preflabel_lazy('time'))
    time_to = fields.Time(title=get_preflabel_lazy('time'))

    __model__ = DateTimeLocationModel


class LocationSchema(BaseSchema):
    location = get_location_field({'order': 1})
    location_description = get_location_description_field({'field_format': 'half', 'order': 2})

    __model__ = DateTimeLocationModel


class DateLocationSchema(BaseSchema):
    date = get_date_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'order': 3})

    __model__ = DateTimeLocationModel


class DateRangeLocationSchema(BaseSchema):
    date = get_date_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})

    __model__ = DateTimeLocationModel


class DateRangeTimeRangeLocationSchema(BaseSchema):
    date = get_date_range_time_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})

    __model__ = DateTimeLocationModel


class DateTimeRangeLocationSchema(BaseSchema):
    date = get_date_time_range_field({'order': 1})
    location = get_location_field({'order': 2})
    location_description = get_location_description_field({'field_format': 'half', 'order': 3})

    __model__ = DateTimeLocationModel


class ContributorModel(GenericModel):
    def to_display(self, roles=False):
        if self.label:
            if roles:
                lang = get_language()
                return {
                    'label': self.label,
                    'value': [
                        getattr(x.label, lang) if x.label else get_preflabel(x.source.split('/')[-1])
                        for x in self.roles
                    ]
                    if self.roles
                    else None,
                }
            return self.label


class ContributorSchema(BaseSchema):
    source = fields.Str(**{'x-attrs': {'hidden': True}})
    label = fields.Str()
    roles = fields.List(fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False))

    __model__ = ContributorModel
