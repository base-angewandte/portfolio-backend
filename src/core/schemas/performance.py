from marshmallow import Schema

from .general import get_contributors_field, get_contributors_field_for_role, get_url_field, \
    get_date_range_time_range_location_group_field, get_material_field, get_format_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Performance',
    'Theaterstück',
    'Aufführung',
    'Intervention',
    'Live Art',
    'Performance Art',
    'Solo-Performance',
    'Tanzperformance',
]


class PerformanceSchema(Schema):
    artist = get_contributors_field_for_role('artist', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 3})
    material = get_material_field({'order': 4})
    format = get_format_field({'order': 5})
    url = get_url_field({'order': 6, 'field_format': 'half'})
