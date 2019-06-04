from marshmallow import Schema

from ..general import get_contributors_field, get_contributors_field_for_role, get_url_field, \
    get_date_range_time_range_location_group_field
from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members

ICON = ICON_EVENT

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_workshop', use_cache=False)


class WorkshopSchema(Schema):
    organiser = get_contributors_field_for_role('organiser_management', {'order': 1})
    lecture = get_contributors_field_for_role('lecture', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 4})
    url = get_url_field({'order': 5})
