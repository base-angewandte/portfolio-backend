from marshmallow import Schema

from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_range_time_range_location_group_field,
    get_format_field,
    get_material_field,
    get_url_field,
)

ICON = ICON_EVENT

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_performance', use_cache=False)


class PerformanceSchema(Schema):
    artists = get_contributors_field_for_role('artist', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 3})
    material = get_material_field({'order': 4})
    format = get_format_field({'order': 5})
    url = get_url_field({'order': 6, 'field_format': 'half'})
