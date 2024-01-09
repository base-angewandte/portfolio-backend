from ...skosmos import get_collection_members, get_preflabel_lazy
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
    get_string_field,
    get_url_field,
)
from ..utils import years_from_date_location_group_field

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_film_video',
    use_cache=False,
)


class VideoSchema(BaseSchema):
    directors = get_contributors_field_for_role('director', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    published_in = get_published_in_field({'order': 3})
    url = get_url_field({'order': 4, 'field_format': 'half'})
    isan = get_string_field(get_preflabel_lazy('isan'), {'order': 5})
    date_location = get_date_location_group_field({'order': 6})
    duration = get_duration_field({'order': 7})
    language = get_language_list_field({'order': 8})
    material = get_material_field({'order': 9, 'field_format': 'half'})
    format = get_format_field({'order': 10})

    def year_display(self, data):
        if data.get('date_location'):
            return years_from_date_location_group_field(data['date_location'])
