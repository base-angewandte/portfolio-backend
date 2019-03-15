from django.conf import settings
from django.urls import reverse_lazy
from marshmallow import Schema, fields

from .general import ContributorSchema, GEOReferenceSchema, DateSchema
from ..skosmos import get_preflabel_lazy, get_uri

# TODO use concept ids as keys
TYPES = [
    'Monographie',
    'Periodikum',
    'Sammelband',
    'Aufsatzsammlung',
    'Künstlerbuch',
    'Zeitungsbericht',
    'Interview',
    'Zeitungsartikel',
    'Kolumne',
    'Blog',
    'Ausstellungskatalog',
    'Katalog',
    'Rezension',
    'Kritik',
    'Beitrag in Sammelband',
    'Aufsatz',
    'Beitrag in Fachzeitschrift (SCI,  SSCI, A&HCI)',
    'Masterarbeit',
    'Diplomarbeit',
    'Dissertation',
    'Bachelorarbeit',
    'Essay',
    'Studie',
    'Tagungsbericht',
    'Kommentar',
    'Fanzine',
    'Buchreihe',
    'Schriftenreihe',
    'Edition',
    'Drehbuch',
    'Libretto',
    'Gutachten',
    'Clipping',
    'Zeitschrift',
    'Magazin',
    'Archivalie',
    'Printbeitrag',
    'Onlinebeitrag',
    'wissenschaftliche Veröffentlichung',
    'künstlerische Veröffentlichung',
    'Katalog/künstlerisches Druckwerk',
    'künstlerischer Ton-/Bild-/Datenträger',
    'Beitrag zu künstlerischem Ton-/Bild-/Datenträger',
]


class PublishedInSchema(Schema):
    title = fields.Str(
        title=get_preflabel_lazy('collection_title'),
        **{'x-attrs': {
            'order': 1,
            'field_format': 'half',
        }},
    )
    subtitle = fields.Str(
        title=get_preflabel_lazy('collection_subtitle'),
        **{'x-attrs': {
            'order': 2,
            'field_format': 'half',
        }},
    )
    editors = fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy('editor'),
        **{'x-attrs': {
            'order': 3,
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributor'}),
            'equivalent': 'contributors',
            'default_role': get_uri('editor'),
            'sortable': True
        }},
    )
    publisher = fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy('publisher'),
        **{'x-attrs': {
            'order': 4,
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributor'}),
            'equivalent': 'contributors',
            'default_role': get_uri('publisher'),
        }},
    )


class DocumentSchema(Schema):
    authors = fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy('authors'),
        **{'x-attrs': {
            'order': 1,
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributor'}),
            'equivalent': 'contributors',
            'default_role': get_uri('authors'),
            'sortable': True,
        }},
    )
    editors = fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy('editor'),
        **{'x-attrs': {
            'order': 2,
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributor'}),
            'equivalent': 'contributors',
            'default_role': get_uri('editor'),
            'sortable': True
        }},
    )
    publisher = fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy('publisher'),
        **{'x-attrs': {
            'order': 3,
            'field_type': 'chips',
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributor'}),
            'equivalent': 'contributors',
            'default_role': get_uri('publisher'),
        }},
    )
    date = fields.Nested(
        DateSchema,
        title=get_preflabel_lazy('collection_date'),
        **{'x-attrs': {
            'order': 4,
            'field_type': 'date',
            'field_format': 'half',
        }},
    )
    location = fields.List(
        fields.Nested(GEOReferenceSchema, additionalProperties=False),
        title=get_preflabel_lazy('collection_location'),
        **{'x-attrs': {
            'order': 5,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'place'}),
            'field_type': 'chips',
            'field_format': 'half',
        }},
    )
    isbn = fields.Str(
        title=get_preflabel_lazy('collection_isbn'),
        **{'x-attrs': {
            'order': 6,
            'field_format': 'half',
        }},
    )
    doi = fields.Str(
        title=get_preflabel_lazy('collection_doi'),
        **{'x-attrs': {
            'order': 7,
            'field_format': 'half',
        }},
    )
    url = fields.Str(
        title=get_preflabel_lazy('collection_url'),
        **{'x-attrs': {
            'order': 8,
            'field_format': 'half',
        }},
    )
    published_in = fields.List(
        fields.Nested(PublishedInSchema, additionalProperties=False),
        title=get_preflabel_lazy('collection_published_in'),
        **{'x-attrs': {
            'order': 9,
            'field_type': 'group',
            'show_label': True,
        }},
    )
    volume = fields.Str(
        title=get_preflabel_lazy('collection_volume_issue'),
        **{'x-attrs': {
            'order': 10,
            'field_format': 'half',
        }},
    )
    pages = fields.Str(
        title=get_preflabel_lazy('collection_pages'),
        **{'x-attrs': {
            'order': 11,
            'field_format': 'half',
        }},
    )
    contributors = fields.List(
        fields.Nested(ContributorSchema, additionalProperties=False),
        title=get_preflabel_lazy('collection_contributor'),
        **{'x-attrs': {
            'order': 12,
            'source': reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'contributor'}),
            'field_type': 'chips-below',
        }},
    )
    language = fields.List(
        fields.Str(),
        title=get_preflabel_lazy('collection_title'),
        **{'x-attrs': {
            'order': 8,
            'field_type': 'chips',
            'source': 'vocbench',
            'field_format': 'half',
        }},
    )
    material = fields.List(
        fields.Str(),
        title=get_preflabel_lazy('collection_material'),
        **{'x-attrs': {
            'order': 14,
            'field_type': 'chips',
            'source': 'vocbench',
        }},
    )
    format = fields.List(
        fields.Str(),
        title=get_preflabel_lazy('collection_format'),
        **{'x-attrs': {
            'order': 15,
            'field_type': 'chips',
            'source': 'vocbench',
            'field_format': 'half',
        }},
    )
    edition = fields.Str(
        title=get_preflabel_lazy('collection_edition'),
        **{'x-attrs': {
            'order': 16,
            'field_format': 'half',
        }},
    )
