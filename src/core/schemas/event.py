from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema

# TODO use concept ids as keys
TYPES = [
    'Auslandsaufenthalt',
    'Buchpräsentation',
    'Premiere',
    'Screening',
    'Sneak Preview',
    'Filmvorführung',
    'Vorschau',
    'Release',
    'Vorpremiere',
    'Vorführung',
    'Pressevorführung',
    'Pressekonferenz',
    'ExpertInnentätigkeit',
    'Live-Präsentation',
    'Medienbeitrag',
    'Veranstaltung',
    'Arbeitsschwerpunkt/laufendes Projekt',
]


class EventSchema(Schema):
    contributors = fields.List(fields.Nested(ContributorSchema, additionalProperties=False), **{'x-attrs': {
        'order': 1,
        'field_type': 'chips-below',
        'source': 'http://localhost:8200/autosuggest/v1/person/',
    }})
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(**{'x-attrs': {'order': 3}})
