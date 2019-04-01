from marshmallow import Schema, fields

from .general import DateRangeSchema, get_contributors_field, get_contributors_field_for_role, get_url_field
from ..schemas import ICON_EVENT

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Drittmittelprojekt',
    'Projekt',
    'Forschungsprojekt',
    'Artistic Research',
]


class ResearchProjectSchema(Schema):
    project_lead = get_contributors_field_for_role('project_lead', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    funding = get_contributors_field_for_role('funding', {'order': 3})
    funding_category = fields.Str(**{'x-attrs': {'order': 4}})
    date = fields.Nested(DateRangeSchema, additionalProperties=False, **{'x-attrs': {'order': 5, 'field_type': 'date'}})
    url = get_url_field({'order': 6})
