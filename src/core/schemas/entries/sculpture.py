from ...skosmos import get_collection_members
from ..base import BaseSchema
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_location_group_field,
    get_dimensions_field,
    get_format_field,
    get_material_field,
    get_url_field,
)

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_sculpture', use_cache=False)


class SculptureSchema(BaseSchema):
    artists = get_contributors_field_for_role('artist', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    date_location = get_date_location_group_field({'order': 3})
    material = get_material_field({'order': 4})
    format = get_format_field({'order': 5})
    dimensions = get_dimensions_field({'order': 6})
    url = get_url_field({'order': 7})
