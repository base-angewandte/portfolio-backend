from marshmallow import fields

from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members, get_preflabel_lazy
from ..base import BaseSchema
from ..general import (
    get_contributors_field,
    get_contributors_field_for_role,
    get_date_range_field,
    get_date_time_range_field,
    get_location_description_field,
    get_location_field,
    get_url_field,
)
from ..utils import years_list_from_date_range, years_to_string

ICON = ICON_EVENT

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_exhibition', use_cache=False)


class DateOpeningLocationSchema(BaseSchema):
    date = get_date_range_field({'order': 1, 'field_format': 'full'})
    opening = get_date_time_range_field({'order': 2}, label=get_preflabel_lazy('opening'))
    location = get_location_field({'order': 3})
    location_description = get_location_description_field({'field_format': 'half', 'order': 4})


class ExhibitionSchema(BaseSchema):
    artists = get_contributors_field_for_role('artist', {'order': 1})
    curators = get_contributors_field_for_role('curator', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    date_opening_location = fields.List(
        fields.Nested(DateOpeningLocationSchema, additionalProperties=False),
        title=format_lazy(
            '{date}, {opening} {conjunction} {location}',
            date=get_preflabel_lazy('date'),
            opening=get_preflabel_lazy('opening'),
            conjunction=_('and'),
            location=get_preflabel_lazy('location'),
        ),
        **{'x-attrs': {
            'field_type': 'group',
            'order': 4,
            'show_label': False,
            'locations_info': True,
        }},
    )
    url = get_url_field({'order': 5})

    def year_display(self, data):
        if data.get('date'):
            years = []
            for dol in data['date']:
                if dol.get('date'):
                    years += years_list_from_date_range(dol['date'])
            if years:
                return years_to_string(years)
