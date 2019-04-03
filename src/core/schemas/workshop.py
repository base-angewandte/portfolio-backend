from marshmallow import Schema

from .general import get_contributors_field, get_contributors_field_for_role, get_url_field, \
    get_date_range_time_range_location_group_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Kinderunikunst',
    'Weiterbildung',
    'Kurs',
    'Seminar',
    'postgraduales Studienangebot',
    'Doktoratsstudium',
    'Einzelcoaching',
    'individuelle Maßnahme',
    'projektorientierte Lehrtätigkeit',
    'Interdisziplinäre Lehrtätigkeit',
    'Interdisziplinäre / projektorientierte Lehrtätigkeit',
]


class WorkshopSchema(Schema):
    organiser = get_contributors_field_for_role('organiser_management', {'order': 1})
    lecture = get_contributors_field_for_role('lecture', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 4})
    url = get_url_field({'order': 5})
