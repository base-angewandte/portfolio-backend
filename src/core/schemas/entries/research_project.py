from marshmallow import fields

from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members
from ..base import BaseSchema
from ..general import get_contributors_field, get_contributors_field_for_role, get_date_range_field, get_url_field

ICON = ICON_EVENT

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project',
    use_cache=False,
)


class ResearchProjectSchema(BaseSchema):
    project_lead = get_contributors_field_for_role('project_lead', {'order': 1})
    project_partnership = get_contributors_field_for_role('project_partnership', {'order': 2})
    funding = get_contributors_field_for_role('funding', {'order': 3})
    funding_category = fields.Str(**{'x-attrs': {'order': 4}})
    contributors = get_contributors_field({'order': 5})
    date = get_date_range_field({'order': 6, 'field_format': 'full'})
    url = get_url_field({'order': 7})
