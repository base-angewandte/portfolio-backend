from marshmallow import Schema

from ..general import get_contributors_field, get_contributors_field_for_role, get_url_field, \
    get_date_range_time_range_location_group_field, get_string_field
from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members, get_preflabel_lazy

ICON = ICON_EVENT

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_contribution',
    use_cache=False,
)


class ConferenceContributionSchema(Schema):
    lecturer = get_contributors_field_for_role('lecturer', {'order': 1})
    title_of_event = get_string_field(get_preflabel_lazy('title_of_event'), {'order': 2})
    organiser = get_contributors_field_for_role('organiser_management', {'order': 3})
    contributors = get_contributors_field({'order': 4})
    date_range_time_range_location = get_date_range_time_range_location_group_field({'order': 5})
    url = get_url_field({'order': 6})
