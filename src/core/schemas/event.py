from marshmallow import Schema, fields

from .general import DateRangeLocationSchema, get_contributors_field, get_url_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

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
    contributors = get_contributors_field({'order': 1})
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 2,
        'field_type': 'group',
        'show_label': False,
    }})
    url = get_url_field({'order': 3})
