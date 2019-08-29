from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members, get_preflabel_lazy
from ..base import BaseSchema
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_location_group_field,
    get_date_time_field,
    get_string_field,
    get_url_field,
)
from ..utils import years_from_date_location_group_field

ICON = ICON_EVENT

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_awards_and_grants',
    use_cache=False,
)


class AwardSchema(BaseSchema):
    category = get_string_field(get_preflabel_lazy('category'), {'order': 1})
    winners = get_contributors_field_for_role('winner', {'order': 2})
    granted_by = get_contributors_field_for_role('granted_by', {'order': 3})
    jury = get_contributors_field_for_role('jury', {'order': 4})
    contributors = get_contributors_field({'order': 5})
    date_location = get_date_location_group_field({'order': 6})
    award_ceremony = get_date_time_field({'field_format': 'half', 'order': 7})
    url = get_url_field({'order': 9, 'field_format': 'half'})

    def year_display(self, data):
        if data.get('date_location'):
            return years_from_date_location_group_field(data['date_location'])
