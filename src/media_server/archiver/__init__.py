import logging
from json import dumps, loads

import requests
import yaml
from django_rq import job

from django.conf import settings
from django.template import loader

from core.models import Entry
from media_server.archiver.choices import STATUS_ARCHIVE_ERROR, STATUS_ARCHIVED

uris = settings.ARCHIVE_URIS
credentials = settings.ARCHIVE_CREDENTIALS


def archive_entry(entry):
    """Calls the respective archival method as configured."""
    template_name = settings.ARCHIVE_THESIS_TEMPLATE if entry.is_thesis else settings.ARCHIVE_METADATA_TEMPLATE
    if settings.ARCHIVE_TYPE == 'PHAIDRA':
        return phaidra_archive_entry(entry, template_name)


@job
def archive_media(media):
    """Calls the respective archival method as configured."""
    if settings.ARCHIVE_TYPE == 'PHAIDRA':
        return phaidra_archive_media(media)


def _map_container_template_data(entry, template_name):
    template = loader.get_template(template_name)
    context = {'entry': entry}
    # Using yaml safe_load instead of json.loads
    # because template rendered json may contain trailing commas
    container_metadata = yaml.safe_load(template.render(context))
    return container_metadata


def _phaidra_create_container(container_metadata):
    res = requests.post(
        uris.get('CREATE_URI'),
        files={'metadata': dumps(container_metadata)},
        auth=(credentials.get('USER'), credentials.get('PWD')),
    )
    return res


def _phaidra_update_container(container_metadata, archive_id):
    """Updates the metadata of a container object in Phaidra."""
    res = requests.post(
        uris.get('BASE_URI') + f'object/{archive_id}/metadata',
        files={'metadata': dumps(container_metadata)},
        auth=(credentials.get('USER'), credentials.get('PWD')),
    )
    return res


def phaidra_archive_entry(entry, template_name):
    """Archive the entry in Phaidra by creating or updating the container
    object."""
    try:
        container_metadata = _map_container_template_data(entry, template_name)
    except ValueError as ve:
        logging.info('Error mapping metadata using %s\n%s', template_name, str(ve))
        return {'Error': str(ve)}

    # if the entry is not already archived as a container, create a container object
    if not entry.archive_id:
        res = _phaidra_create_container({'metadata': {'json-ld': {'container': container_metadata}}})
        if res.status_code != 200:
            logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
            return res

        pid = loads(res.content).get('pid', '')
        if pid.strip():
            entry.archive_URI = uris.get('IDENTIFIER_BASE') + pid
            entry.archive_id = pid
            entry.save(update_fields=['archive_URI', 'archive_id'])
        else:
            logging.warning('NO PID returned in response, %s', res.content)
    else:
        # Assume that there is a metadata change and update the container metadata
        # instead update metadata should be called whenever the entry metadata is updated in Portfolio
        res = _phaidra_update_container({'metadata': {'json-ld': container_metadata}}, entry.archive_id)
        if res.status_code != 200:
            logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
            return res

    return {'entry_pid': entry.archive_id}


def phaidra_archive_media(media):
    """Archives the given media in Phaidra and returns the persistent id for.

    - the container (entry_pid) and
    - the media (media_pid)
    """
    # Find associated entry object for this asset
    entry = Entry.objects.get(id=media.entry_id)
    if not entry.archive_id:
        logging.warning('Entry %s not yet archived, cannot archive media %s', entry.id, media, id)
        return {'Error': 'Entry {entry.id} not yet archived, cannot archive media %s'}
    if not media.archive_id:
        # media already archived and linked to entry object
        # TODO: Are we really sure that in PHAIDRA
        # this media asset linked to its respective container?

        # Create a media object separately

        post_url = uris.get(media.type, 'x')

        template = loader.get_template('phaidra_member.json')
        context = {'media': media}
        member_metadata = loads(template.render(context))

        res = requests.post(
            post_url,
            files={
                'metadata': dumps(member_metadata),
                'file': media.file,
            },
            auth=(credentials.get('USER'), credentials.get('PWD')),
        )

        if res.status_code != 200:
            media.archive_status = STATUS_ARCHIVE_ERROR
            media.save()
            logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
            return res

        pid = loads(res.content).get('pid', '')
        if pid.strip():
            media.archive_URI = uris.get('IDENTIFIER_BASE') + pid
            media.archive_id = pid
            media.archive_status = STATUS_ARCHIVED
            media.save()

            # Add member to container
            link_member_url = uris.get('BASE_URI') + f'object/{entry.archive_id}/relationship/add'

            res = requests.post(
                link_member_url,
                {'predicate': 'http://pcdm.org/models#hasMember', 'object': f'info:fedora/{media.archive_id}'},
                auth=(credentials.get('USER'), credentials.get('PWD')),
            )

            if res.status_code != 200:
                logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
                return res
            else:
                pass
        else:
            logging.warning('NO PID returned in response, %s', res.content)

    # If the media has already been archived and recorded in the database, this method silently returns with the pids
    return {'entry_pid': entry.archive_id, 'media_pid': media.archive_id}
