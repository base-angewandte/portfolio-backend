from django.urls import reverse_lazy
from marshmallow import Schema, fields

from ..general import get_contributors_field, get_contributors_field_for_role, get_date_field, get_url_field, \
    validate_year, get_string_field, get_field, SourceMultilingualLabelSchema
from ...skosmos import get_collection_members, get_preflabel_lazy
from ...utils import placeholder_lazy

TYPES = get_collection_members('http://base.uni-ak.ac.at/portfolio/taxonomy/collection_software', use_cache=False)


class SoftwareSchema(Schema):
    software_developer = get_contributors_field_for_role('software_developer', {'order': 1})
    programming_language = get_string_field(
        get_preflabel_lazy('programming_language'),
        {
            'field_format': 'half',
            'order': 2,
        },
    )
    open_source_license = fields.Nested(
        SourceMultilingualLabelSchema,
        title=get_preflabel_lazy('open_source_license'),
        additionalProperties=False,
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'softwarelicenses'}),
            'placeholder': placeholder_lazy(get_preflabel_lazy('open_source_license')),
            'order': 3,
        }},
    )
    lines_of_code = get_field(
        fields.Int,
        get_preflabel_lazy('lines_of_code'),
        {
            'field_format': 'half',
            'order': 4,
        },
    )
    software_version = get_string_field(
        get_preflabel_lazy('software_version'),
        {
            'field_format': 'half',
            'order': 5,
        },
    )
    git_url = get_field(
        fields.Url,
        get_preflabel_lazy('git_url'),
        {'order': 6},
    )
    documentation_url = get_field(
        fields.Url,
        get_preflabel_lazy('documentation_url'),
        {'order': 7},
    )
    contributors = get_contributors_field({'order': 8})
    date = get_date_field({'order': 9, 'date_format': 'year'}, validator=validate_year)
    url = get_url_field({'order': 10, 'field_format': 'half'})
