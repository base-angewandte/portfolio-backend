import logging

import requests

from django.conf import settings

from core.models import Entry
from media_server.models import AUDIO_TYPE, DOCUMENT_TYPE, IMAGE_TYPE, STATUS_CONVERTED, VIDEO_TYPE, Media

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
    entry.refresh_from_db()
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

    if r.status_code == 201:
        response = r.json()
        handle_push_entry_response(response)

        # if the entry was just created in Showroom, we also have to push media and relations
        if response.get('created'):
            published_media = Media.objects.filter(entry_id=entry.id, published=True, status=STATUS_CONVERTED)
            for medium in published_media:
                try:
                    push_medium(medium)
                except ShowroomError as err:
                    logger.warning(f'Problem encountered when syncing medium for entry {entry.id}: {err}')
            try:
                push_relations(entry)
            except ShowroomError as err:
                logger.warning(f'Problem encountered when syncing relations for entry {entry.id}: {err}')
            # push_relations only pushes the relations of an entry to attached entries. but
            # if the currently published entry is attached to other already published entries
            # we have to update the relations of those as well
            published_parent_relations = entry.to_entries.filter(from_entry__published=True)
            for relation in published_parent_relations:
                try:
                    push_relations(e := relation.from_entry)
                except ShowroomError as err:
                    logger.warning(f'Problem encountered when syncing relations for entry {e.id} (parent): {err}')
        return response

    elif r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 400:
        raise ShowroomError(f'Entry {entry.id} could not be pushed: 400: {r.text}')
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def delete_entry(entry):
    r = requests.delete(settings.SHOWROOM_API_BASE + f'activities/{entry.id}/', headers=auth_headers)
    if r.status_code == 204:
        Entry.objects.filter(pk=entry.pk).update(showroom_id=None)
        return True
    elif r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 404:
        # in case we want to delete an object that cannot be found in Showroom, we'll just log this as a warning
        # because the desired state is already achieved, but something else seems to be off
        logger.warning(f'Entry {entry.id} could not be deleted because not found in Showroom [404]')
    elif r.status_code == 400:
        raise ShowroomError(f'Entry {entry.id} could not be deleted: 400: {r.text}')
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
        'featured': medium.featured,
        'order': medium.order,
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

    if r.status_code == 201:
        return r.json()
    elif r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 400:
        raise ShowroomError(f'Medium {medium.id} could not be pushed: 400: {r.text}')
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def delete_medium(medium):
    r = requests.delete(settings.SHOWROOM_API_BASE + f'media/{medium.id}/', headers=auth_headers)
    if r.status_code == 204:
        return True
    elif r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 404:
        # in case we want to delete an object that cannot be found in Showroom, we'll just log this as a warning
        # because the desired state is already achieved, but something else seems to be off
        logger.warning(f'Medium {medium.id} could not be deleted because not found in Showroom [404]')
    elif r.status_code == 400:
        raise ShowroomError(f'Medium {medium.id} could not be deleted: 400: {r.text}')
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def push_relations(entry):
    data = {'related_to': [rel.to_entry.id for rel in entry.from_entries.filter(to_entry__published=True)]}
    print(f'pushing relations for {entry.id} to {data["related_to"]}')
    r = requests.post(f'{settings.SHOWROOM_API_BASE}activities/{entry.id}/relations/', json=data, headers=auth_headers)

    if r.status_code == 201:
        return r.json()
    elif r.status_code == 404:
        raise ShowroomError(f'Could not push relations for Entry {entry.id}: 404: {r.text}')
    elif r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 400:
        raise ShowroomError(f'Could not push relations for Entry {entry.id}: 400: {r.text}')
    else:
        raise ShowroomUndefinedError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def handle_push_entry_response(response):
    """Update portfolio entries based on result of push to Showroom.

    When entries are pushed to Showroom, the response will contain a
    list of created and updated Showroom activity IDs. For newly
    published entries we need to store the (new) activity ID. The
    updated Showroom activities can be ignored as we already stored the
    ID, when the activity was created.
    """
    created = response.get('created', [])
    for item in created:
        Entry.objects.filter(pk=item['id']).update(showroom_id=item['showroom_id'])
