from marshmallow import Schema

from .general import get_contributors_field, get_url_field, get_date_range_time_range_location_group_field
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
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 2})
    url = get_url_field({'order': 3})
