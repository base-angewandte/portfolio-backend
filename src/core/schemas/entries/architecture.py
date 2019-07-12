from marshmallow import Schema

from ...skosmos import get_collection_members
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_location_group_field,
    get_format_field,
    get_material_field,
    get_url_field,
)

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_architecture', use_cache=False)


class ArchitectureSchema(Schema):
    architecture = get_contributors_field_for_role('architecture', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    date_location = get_date_location_group_field({'order': 3})
    material = get_material_field({
        'field_format': 'half',
        'order': 4,
    })
    format = get_format_field({'order': 5})
    url = get_url_field({'order': 6})
