from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members
from ..base import BaseSchema
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_range_location_group_field,
)
from ..utils import years_from_date_range_location_group_field

ICON = ICON_EVENT

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_fellowship_visiting_affiliation',
    use_cache=False,
)


class FellowshipVisitingAffiliationSchema(BaseSchema):
    fellow_scholar = get_contributors_field_for_role('fellow_scholar', {'order': 1})
    funding = get_contributors_field_for_role('funding', {'order': 2})
    organisations = get_contributors_field_for_role('organisation', {'order': 3})
    contributors = get_contributors_field({'order': 4})
    date_range_location = get_date_range_location_group_field({'order': 5})

    def year_display(self, data):
        if data.get('date_range_location'):
            return years_from_date_range_location_group_field(
                data['date_range_location']
            )
