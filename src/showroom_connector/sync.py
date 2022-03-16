import logging

import requests

from django.conf import settings

from . import AUDIO_TYPE, DOCUMENT_TYPE, IMAGE_TYPE, VIDEO_TYPE

logger = logging.getLogger(__name__)


class ShowroomError(Exception):
    pass


class ShowroomAuthenticationError(ShowroomError):
    pass


class ShowroomUndefinedError(ShowroomError):
    pass


class ShowroomNotFoundError(ShowroomError):
    pass


auth_headers = {
    'X-Api-Client': str(settings.SHOWROOM_REPO_ID),
    'X-Api-Key': settings.SHOWROOM_API_KEY,
}


def push_entry(entry):
    data = {
        'source_repo_entry_id': entry.id,
        'source_repo': settings.SHOWROOM_REPO_ID,
        'source_repo_owner_id': str(entry.owner),
        'data': {
            'title': entry.title,
            'subtitle': entry.subtitle,
            'type': entry.type,
            'keywords': entry.keywords,
            'texts': entry.texts,
            'data': entry.data,
        },
    }

    r = requests.post(settings.SHOWROOM_API_BASE + 'activities/', json=data, headers=auth_headers)

    if r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')

    elif r.status_code == 400:
        raise ShowroomError(f'Entry {entry.id} could not be pushed: 400: {r.text}')

    elif r.status_code == 201:
        return r.json()
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def delete_entry(entry):
    r = requests.delete(settings.SHOWROOM_API_BASE + f'activities/{entry.id}/', headers=auth_headers)
    if r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 404:
        # in case we want to delete an object that cannot be found in Showroom, we'll just log this as a warning
        # because the desired state is already achieved, but something else seems to be off
        logger.warning(f'Entry {entry.id} could not be deleted because not found in Showroom [404]')
    elif r.status_code == 400:
        raise ShowroomError(f'Entry {entry.id} could not be deleted: 400: {r.text}')
    elif r.status_code == 204:
        return True
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def push_medium(medium):
    medium_data = medium.get_data()
    data = {
        'file': medium.file.url,
        'type': medium.type,
        'mime_type': medium.mime_type,
        'exif': medium.exif,
        'license': medium.license,
        'source_repo_media_id': medium.id,
        'source_repo_entry_id': medium.entry_id,
        'specifics': {},
    }
    if medium.type == IMAGE_TYPE:
        data['specifics'] = {
            'previews': medium_data.get('previews'),
            'thumbnail': medium_data.get('thumbnail'),
        }
    elif medium.type == AUDIO_TYPE:
        data['specifics'] = {
            'duration': medium_data['metadata'].get('Duration'),
            'mp3': medium_data.get('mp3'),
        }
    elif medium.type == VIDEO_TYPE:
        data['specifics'] = {
            'duration': medium_data['metadata'].get('Duration'),
            'cover': medium_data.get('cover'),
            'poster': medium_data.get('poster'),
            'playlist': medium_data.get('playlist'),
        }
    elif medium.type == DOCUMENT_TYPE:
        data['specifics'] = {
            'cover': medium_data.get('cover'),
            'pdf': medium_data.get('pdf'),
            'thumbnail': medium_data.get('thumbnail'),
        }

    r = requests.post(settings.SHOWROOM_API_BASE + 'media/', json=data, headers=auth_headers)

    if r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 400:
        raise ShowroomError(f'Medium {medium.id} could not be pushed: 400: {r.text}')
    elif r.status_code == 201:
        return r.json()
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def delete_medium(medium):
    r = requests.delete(settings.SHOWROOM_API_BASE + f'media/{medium.id}/', headers=auth_headers)
    if r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 404:
        # in case we want to delete an object that cannot be found in Showroom, we'll just log this as a warning
        # because the desired state is already achieved, but something else seems to be off
        logger.warning(f'Medium {medium.id} could not be deleted because not found in Showroom [404]')
    elif r.status_code == 400:
        raise ShowroomError(f'Medium {medium.id} could not be deleted: 400: {r.text}')
    elif r.status_code == 204:
        return True
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def push_relations(entry):
    data = {'related_to': [rel.to_entry.id for rel in entry.from_entries.all()]}
    r = requests.post(f'{settings.SHOWROOM_API_BASE}activities/{entry.id}/relations/', json=data, headers=auth_headers)

    if r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 400:
        raise ShowroomError(f'Could not push relations for Entry {entry.id}: 400: {r.text}')
    elif r.status_code == 201:
        # TODO: showroom is returning a dict with `created` and `not_found` arrays containing the
        #       ids of those relations added and those entries that could not be found. in theory
        #       `not_found` should be empty. but if not, how shall we handle this?
        return r.json()
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')
