import requests

from django.conf import settings


class ShowroomError(Exception):
    pass


class ShowroomAuthenticationError(ShowroomError):
    pass


class ShowroomNotFoundError(Exception):
    pass


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

    headers = {
        'X-Api-Client': str(settings.SHOWROOM_REPO_ID),
        'X-Api-Key': settings.SHOWROOM_API_KEY,
    }
    r = requests.post(settings.SHOWROOM_API_BASE + 'activities/', json=data, headers=headers)

    if r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')

    elif r.status_code == 400:
        raise ShowroomError(f'Entry {entry.id} could not be pushed: 400: {r.text}')

    elif r.status_code == 201:
        return True
    else:
        raise ShowroomError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')


def delete_entry(entry):
    headers = {
        'X-Api-Client': str(settings.SHOWROOM_REPO_ID),
        'X-Api-Key': settings.SHOWROOM_API_KEY,
    }
    r = requests.delete(settings.SHOWROOM_API_BASE + f'activities/{entry.id}/', headers=headers)
    if r.status_code == 403:
        raise ShowroomAuthenticationError(f'Authentication failed: {r.text}')
    elif r.status_code == 404:
        raise ShowroomNotFoundError(f'Entry {entry.id} could not be found. 404')
    elif r.status_code == 400:
        raise ShowroomError(f'Entry {entry.id} could not be pushed: 400: {r.text}')
    elif r.status_code == 204:
        print(f'deleted {entry.id}')
        return True
    else:
        raise ShowroomError(f'Ouch! Something unexpected happened: {r.status_code} {r.text}')
