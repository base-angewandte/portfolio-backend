import logging
from json import dumps, loads

import requests

from django.conf import settings
from django.template import loader

from core.models import Entry
from core.skosmos import get_equivalent_concepts
from media_server.models import AUDIO_TYPE, DOCUMENT_TYPE, IMAGE_TYPE, VIDEO_TYPE

uris = settings.ARCHIVE_URIS
credentials = settings.ARCHIVE_CREDENTIALS


def archive(media, template_name):
    """
    Calls the respective archival method as configured
    """
    if settings.ARCHIVE_TYPE == 'PHAIDRA':
        return phaidra_archive(media, template_name)


def _map_container_template_data(entry, template_name):
    template = loader.get_template(template_name)
    context = {'entry': entry}
    # Cannot use json.loads because there is a trailing comma after last element
    # that is generated by template rendering
    container_metadata = eval(template.render(context))
    return container_metadata


def _phaidra_create_container(container_metadata):
    res = requests.post(
        uris.get('CREATE_URI'),
        files={'metadata': dumps(container_metadata)},
        auth=(credentials.get('USER'), credentials.get('PWD')),
    )
    return res


def _phaidra_update_container(container_metadata, archive_id):
    """
    Updates the metadata of a container object in Phaidra
    """
    res = requests.post(
        uris.get('BASE_URI') + f'object/{archive_id}/metadata',
        files={'metadata': dumps(container_metadata)},
        auth=(credentials.get('USER'), credentials.get('PWD')),
    )
    return res


def phaidra_archive(media, template_name):
    """
    Archives the given media in Phaidra and
    returns the persistent id for
    - the container (entry_pid) and
    - the media (media_pid)
    TODO - PERFORMACE: What happens to the POST request when the file size of the media is too big
    FIXME - Updating metadata in a container does not work as expected.
    """
    # Find associated entry object for this asset
    entry = Entry.objects.get(id=media.entry_id)
    try:
        container_metadata = _map_container_template_data(entry, template_name)
        # return container_metadata
    except ValueError as ve:
        return {'Error': str(ve)}

    # if the entry is not already archived as a container, create a container object
    if not entry.archive_id:
        res = _phaidra_create_container({"metadata": {"json-ld": {"container": container_metadata}}})
        if res.status_code != 200:
            logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
            return res

        pid = loads(res.content).get('pid', '')
        if pid.strip():
            entry.archive_URI = uris.get('BASE_URI') + pid
            entry.archive_id = pid
            entry.save()
        else:
            logging.warning('NO PID returned in response, %s', res.content)
    else:
        # Assume that there is a metadata change and update the container metadata
        # FIXME: This should not be here;
        # instead update metadata should be called whenever the entry metadata is updated in Portfolio
        res = _phaidra_update_container({"metadata": {"json-ld": container_metadata}}, entry.archive_id)
        if res.status_code != 200:
            logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
            return res

    if not media.archive_id:
        # media already archived and linked to entry object
        # TODO: Are we really sure that in PHAIDRA
        # this media asset linked to its respective container?

        # Create a media object separately
        if media.type == IMAGE_TYPE:
            post_url = uris.get('PICTURE_CREATE')
        elif media.type == AUDIO_TYPE:
            post_url = uris.get('AUDIO_CREATE')
        elif media.type == VIDEO_TYPE:
            post_url = uris.get('VIDEO_CREATE')
        elif media.type == DOCUMENT_TYPE:
            post_url = uris.get('DOCUMENT_CREATE')
        else:
            post_url = uris.get('OBJECT_CREATE')

        template = loader.get_template('phaidra_member.json')
        context = {'media': media}
        member_metadata = eval(template.render(context))

        res = requests.post(
            post_url,
            files={
                'metadata': dumps(member_metadata),
                'file': media.file,
            },
            auth=(credentials.get('USER'), credentials.get('PWD')),
        )

        if res.status_code != 200:
            logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
            return res

        pid = loads(res.content).get('pid', '')
        if pid.strip():
            media.archive_URI = uris.get('BASE_URI') + pid
            media.archive_id = pid
            media.save()

            # Add member to container
            link_member_url = uris.get("BASE_URI") + f'object/{entry.archive_id}/relationship/add'

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
