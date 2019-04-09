from django.urls import reverse_lazy
from marshmallow import Schema, fields

from core.skosmos import get_preflabel_lazy
from .general import get_contributors_field, get_contributors_field_for_role, get_date_field, get_url_field, \
    validate_year

# TODO use concept ids as keys
TYPES = [
    'Computerprogramm',
    'Client-Server Software',
    'Treiber Software',
    'Handy App',
    'Betriebssystem',
    'Software',
    'Computerspiel',
    'Web Applikation',
]


class SoftwareSchema(Schema):
    software_developer = get_contributors_field_for_role('software_developer', {'order': 1})
    programming_language = fields.Str(
        title=get_preflabel_lazy('programming_language'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 2,
        }},
    )
    open_source_licence = fields.Str(
        title=get_preflabel_lazy('open_source_licence'),
        **{'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'licenses'}),
            'order': 3,
        }},
    )
    lines_of_code = fields.Int(
        title=get_preflabel_lazy('lines_of_code'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 4,
        }},
    )
    software_version = fields.Str(
        title=get_preflabel_lazy('software_version'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 5,
        }},
    )
    git_url = fields.Url(
        title=get_preflabel_lazy('git_url'),
        **{'x-attrs': {
            'order': 6,
        }},
    )
    documentation_url = fields.Url(
        title=get_preflabel_lazy('documentation_url'),
        **{'x-attrs': {
            'order': 7,
        }},
    )
    contributors = get_contributors_field({'order': 8})
    date = get_date_field({'order': 9, 'date_format': 'year'}, validator=validate_year)
    url = get_url_field({'order': 10, 'field_format': 'half'})
