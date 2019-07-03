from marshmallow import Schema, fields

from ..general import get_format_field, get_material_field, get_contributors_field, get_contributors_field_for_role, \
    get_date_field, get_location_field, get_url_field, get_language_list_field, get_string_field
from ...skosmos import get_collection_members, get_preflabel_lazy

TYPES = get_collection_members(
    'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_document_publication',
    use_cache=False,
)


class PublishedInSchema(Schema):
    title = get_string_field(
        get_preflabel_lazy('title'),
        {
            'field_format': 'half',
            'order': 1,
        }
    )
    subtitle = get_string_field(
        get_preflabel_lazy('subtitle'),
        {
            'field_format': 'half',
            'order': 2,
        }
    )
    editor = get_contributors_field_for_role('editor', {'order': 3})
    publisher = get_contributors_field_for_role('publisher', {'order': 4})


class DocumentSchema(Schema):
    authors = get_contributors_field_for_role('author', {'order': 1})
    editors = get_contributors_field_for_role('editor', {'order': 2})
    publishers = get_contributors_field_for_role('publisher', {'order': 3})
    date = get_date_field({'order': 4})
    location = get_location_field({'order': 5})
    isbn = get_string_field(
        get_preflabel_lazy('isbn'),
        {
            'field_format': 'half',
            'order': 6,
        }
    )
    doi = get_string_field(
        get_preflabel_lazy('doi'),
        {
            'field_format': 'half',
            'order': 7,
        }
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
    volume = get_string_field(
        get_preflabel_lazy('volume_issue'),
        {
            'field_format': 'half',
            'order': 10,
        }
    )
    pages = get_string_field(
        get_preflabel_lazy('pages'),
        {
            'field_format': 'half',
            'order': 11,
        }
    )
    contributors = get_contributors_field({'order': 12})
    language = get_language_list_field({'order': 13})
    material = get_material_field({'order': 14, 'field_format': 'half'})
    format = get_format_field({'order': 15})
    edition = get_string_field(
        get_preflabel_lazy('edition'),
        {
            'field_format': 'half',
            'order': 16,
        }
    )
