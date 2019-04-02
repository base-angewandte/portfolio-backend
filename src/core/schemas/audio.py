from marshmallow import Schema

from .general import get_material_field, get_format_field, get_contributors_field, get_contributors_field_for_role, \
    get_url_field, get_language_list_field, get_date_location_group_field, get_published_in_field, get_duration_field

# TODO use concept ids as keys
TYPES = [
    'Podcast',
    'Radiointerview',
    'Radiofeature',
    'Radiobeitrag',
    'Audiobeitrag',
    'Reportage',
    'Hörspiel',
    'Hörbuch',
    'Rundfunkausstrahlung',
    'Radiokunst',
    'Konzertmitschnitt',
    'Studioeinspielung',
    'Tonaufnahme',
    'Audioaufzeichnung',
    'mp3',
    'Kammermusik CD',
    'CD Aufnahme',
    'Album',
    'CD-Box',
]


class AudioSchema(Schema):
    authors = get_contributors_field_for_role('authors', {'order': 1})
    artist = get_contributors_field_for_role('artist', {'order': 2})
    contributors = get_contributors_field({'order': 3})
    published_in = get_published_in_field({'order': 4})
    url = get_url_field({'order': 5})
    date_location = get_date_location_group_field({'order': 6})
    duration = get_duration_field({'order': 7})
    language = get_language_list_field({'order': 8})
    material = get_material_field({'order': 9})
    format = get_format_field({'order': 10})
