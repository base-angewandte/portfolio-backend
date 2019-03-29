from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, DateRangeLocationSchema, get_contributors_field, get_contributors_field_for_role
from ..schemas import ICON_EVENT
from ..skosmos import get_preflabel_lazy

ICON = ICON_EVENT

# TODO use concept ids as keys
TYPES = [
    'Keynote',
    'Konferenzteilnahme',
    'Präsentation',
    'Symposium',
    'Tagung',
    'Konferenz',
    'Vortrag',
    'Talk',
    'Lesung',
    'Gespräch',
    'Artistic Research Meeting',
    'Podiumsdiskussion',
    'Projektpräsentation',
    'Künstler / innengespräch'
    'lecture performance',
]


class ConferenceSchema(Schema):
    organiser = get_contributors_field_for_role('organiser_management', {'order': 1})
    lecture = get_contributors_field_for_role('lecture', {'order': 2})
    title_of_contribution = fields.Str(
        title=get_preflabel_lazy('title_of_paper'),
        **{'x-attrs': {'order': 3}})
    contributors = get_contributors_field({'order': 4})
    # TODO: this should actually also include time!! check again after discussion
    date_location = fields.List(fields.Nested(DateRangeLocationSchema, additionalProperties=False), **{'x-attrs': {
        'order': 5,
        'field_type': 'group',
        'show_label': False,
    }})
    url = fields.Str(title=get_preflabel_lazy('url'), **{'x-attrs': {'order': 6}})
