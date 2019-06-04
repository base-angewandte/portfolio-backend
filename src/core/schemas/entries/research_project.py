from marshmallow import Schema, fields

from ..general import get_contributors_field, get_contributors_field_for_role, get_url_field, get_date_range_field
from ...schemas import ICON_EVENT
from ...skosmos import get_collection_members

ICON = ICON_EVENT

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project',
    use_cache=False,
)


class ResearchProjectSchema(Schema):
    project_lead = get_contributors_field_for_role('project_lead', {'order': 1})
    funding = get_contributors_field_for_role('funding', {'order': 2})
    funding_category = fields.Str(**{'x-attrs': {'order': 3}})
    contributors = get_contributors_field({'order': 4})
    date = get_date_range_field({'order': 5, 'field_format': 'full'})
    url = get_url_field({'order': 6})
