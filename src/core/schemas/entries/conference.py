from marshmallow import Schema

from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members, get_preflabel_lazy
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_range_time_range_location_group_field,
    get_string_field,
    get_url_field,
)

ICON = ICON_EVENT

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference', use_cache=False)


class ConferenceSchema(Schema):
    organisers = get_contributors_field_for_role('organiser_management', {'order': 1})
    lecturers = get_contributors_field_for_role('lecturer', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 4})
    url = get_url_field({'order': 5})
