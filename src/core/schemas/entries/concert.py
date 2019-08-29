from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members
from ..base import BaseSchema
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_time_range_location_group_field,
    get_url_field,
)
from ..utils import years_from_date_time_range_location_group_field

ICON = ICON_EVENT

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_concert', use_cache=False)


class ConcertSchema(BaseSchema):
    music = get_contributors_field_for_role('music', {'order': 1})
    conductors = get_contributors_field_for_role('conductor', {'order': 2})
    composition = get_contributors_field_for_role('composition', {'order': 3})
    contributors = get_contributors_field({'order': 4})
    date_time_range_location = get_date_time_range_location_group_field({'order': 5})
    url = get_url_field({'order': 6})

    def year_display(self, data):
        if data.get('date_time_range_location'):
            return years_from_date_time_range_location_group_field(data['date_time_range_location'])
