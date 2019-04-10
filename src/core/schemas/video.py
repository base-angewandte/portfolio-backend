from marshmallow import Schema

from .general import get_material_field, get_format_field, get_contributors_field, get_contributors_field_for_role, \
    get_language_list_field, get_date_location_group_field, get_published_in_field, get_duration_field, get_url_field

# TODO use concept ids as keys
TYPES = [
    'Fernsehbericht',
    'Dokumentation',
    'Spielfilm',
    'Film',
    'Fernsehbeitrag',
    'TV-Beitrag',
    'Kurzfilm',
    'Videoaufzeichnung',
    'Video',
    'Videoarbeit',
    'Filmarbeit',
    'Animationsfilm',
    'Experimentalfilm',
    'Trailer',
    'Dokumentarfilm',
    'DVD und Blu Ray',
    'Lehrvideo-Einleitung',
    'Lehrvideo',
    'DVD',
    'Vimeo Video',
    'Zeitbasierte Medien'
]


class VideoSchema(Schema):
    director = get_contributors_field_for_role('director', {'order': 1})
    contributors = get_contributors_field({'order': 2})
    published_in = get_published_in_field({'order': 3})
    url = get_url_field({'order': 4, 'field_format': 'half'})
    date_location = get_date_location_group_field({'order': 5})
    duration = get_duration_field({'order': 6})
    language = get_language_list_field({'order': 7})
    material = get_material_field({'order': 8, 'field_format': 'half'})
    format = get_format_field({'order': 9})
