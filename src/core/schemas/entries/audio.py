from ...skosmos import get_collection_members
from ..base import BaseSchema
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_location_group_field,
    get_duration_field,
    get_format_field,
    get_language_list_field,
    get_material_field,
    get_published_in_field,
    get_url_field,
)
from ..utils import years_from_date_location_group_field

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_audio',
    use_cache=False,
)


class AudioSchema(BaseSchema):
    authors = get_contributors_field_for_role('author', {'order': 1})
    artists = get_contributors_field_for_role('artist', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    published_in = get_published_in_field({'order': 4})
    url = get_url_field({'order': 5, 'field_format': 'half'})
    date_location = get_date_location_group_field({'order': 6})
    duration = get_duration_field({'order': 7})
    language = get_language_list_field({'order': 8})
    material = get_material_field({'order': 9, 'field_format': 'half'})
    format = get_format_field({'order': 10})

    def year_display(self, data):
        if data.get('date_location'):
            return years_from_date_location_group_field(data['date_location'])
