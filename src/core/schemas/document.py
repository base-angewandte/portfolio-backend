from marshmallow import Schema, fields

from .general import get_format_field, get_material_field, get_contributors_field, get_contributors_field_for_role, \
    get_date_field, get_location_field, get_url_field, get_language_list_field
from ..skosmos import get_preflabel_lazy

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
        title=get_preflabel_lazy('title'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 1,
        }},
    )
    subtitle = fields.Str(
        title=get_preflabel_lazy('subtitle'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 2,
        }},
    )
    editor = get_contributors_field_for_role('editor', {'order': 3})
    publisher = get_contributors_field_for_role('publisher', {'order': 4})


class DocumentSchema(Schema):
    authors = get_contributors_field_for_role('authors', {'order': 1})
    editors = get_contributors_field_for_role('editor', {'order': 2})
    publisher = get_contributors_field_for_role('publisher', {'order': 3})
    date = get_date_field({'order': 4})
    location = get_location_field({'order': 5})
    isbn = fields.Str(
        title=get_preflabel_lazy('isbn'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 6,
        }},
    )
    doi = fields.Str(
        title=get_preflabel_lazy('doi'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 7,
        }},
    )
    url = get_url_field({'order': 8})
    published_in = fields.List(
        fields.Nested(PublishedInSchema, additionalProperties=False),
        title=get_preflabel_lazy('published_in'),
        **{'x-attrs': {
            'field_type': 'group',
            'show_label': True,
            'order': 9,
        }},
    )
    volume = fields.Str(
        title=get_preflabel_lazy('volume_issue'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 10,
        }},
    )
    pages = fields.Str(
        title=get_preflabel_lazy('pages'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 11,
        }},
    )
    contributors = get_contributors_field({'order': 12})
    language = get_language_list_field({'order': 13})
    material = get_material_field({'order': 14, 'field_format': 'half'})
    format = get_format_field({'order': 15})
    edition = fields.Str(
        title=get_preflabel_lazy('edition'),
        **{'x-attrs': {
            'field_format': 'half',
            'order': 16,
        }},
    )
