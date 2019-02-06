from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema

# TODO use concept ids as keys
TYPES = [
    'Keynote',
    'Konferenzteilnahme',
    'Präsentation',
    'Symposium',
    'Tagung',
    'Konferenz',
    'Vortrag',
    'Talk',
    'Lesung',
    'Gespräch',
    'Artistic Research Meeting',
    'Podiumsdiskussion',
    'Projektpräsentation',
    'Künstler / innengespräch'
    'lecture performance',
]


class ConferenceSchema(Schema):
    organiser = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'organiser'  # TODO: replace with id!
    }})
    lecturer = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'chips',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
        'equivalent': 'contributors',
        'default_role': 'lecturer'  # TODO: replace with id!
    }})
    title_of_contribution = fields.Str(**{'x-attrs': {'order': 3}})
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 4,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    # TODO: this should actually also include time!! check again after discussion
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 5,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 6}})
