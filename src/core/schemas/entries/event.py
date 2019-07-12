from marshmallow import Schema

from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members
from ..general import get_contributors_field, get_date_range_time_range_location_group_field, get_url_field

ICON = ICON_EVENT

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event', use_cache=False)


class EventSchema(Schema):
    contributors = get_contributors_field({'order': 1})
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 2})
    url = get_url_field({'order': 3})
