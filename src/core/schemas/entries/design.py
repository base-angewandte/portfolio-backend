from ...skosmos import get_collection_members
from ..base import BaseSchema
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_location_group_field,
    get_format_field,
    get_material_field,
    get_url_field,
)
from ..utils import years_from_date_location_group_field

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_design', use_cache=False)


class DesignSchema(BaseSchema):
    design = get_contributors_field_for_role('design', {'order': 1})
    commissions = get_contributors_field_for_role('commissions_orders_for_works', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date_location = get_date_location_group_field({'order': 4})
    material = get_material_field({'field_format': 'half', 'order': 5})
    format = get_format_field({'order': 6})
    url = get_url_field({'order': 7})

    def year_display(self, data):
        if data.get('date_location'):
            return years_from_date_location_group_field(data['date_location'])
