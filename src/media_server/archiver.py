import logging
from json import dumps, loads

import requests

from django.conf import settings
from django.template import loader

from core.models import Entry
from media_server.models import AUDIO_TYPE, DOCUMENT_TYPE, IMAGE_TYPE, VIDEO_TYPE, Media, get_media_for_entry


class Archiver:
    def __init__(self):
        self.uris = settings.ARCHIVE_URIS
        self.credentials = settings.ARCHIVE_CREDENTIALS

    def archive(self, media):
        if settings.ARCHIVE_TYPE == 'PHAIDRA':
            return self.phaidra_archive(media)

    def _phaidra_create_container(self, entry):
        template = loader.get_template('phaidra_container.json')
        context = {'entry': entry}

        # Cannot use json.loads because there is a trailing comma after last element
        # that is generated by template rendering
        container_metadata = eval(template.render(context))
        res = requests.post(
            self.uris.get('CREATE_URI'),
            files={'metadata': dumps(container_metadata)},
            auth=(self.credentials.get('USER'), self.credentials.get('PWD')),
        )

        return res

    def _phaidra_update_container(self, entry):
        # curl -X POST -u username:password -F metadata=@metadata.json
        # https://services.phaidra-sandbox.univie.ac.at/api/object/o:123/metadata
        template = loader.get_template('phaidra_container.json')
        context = {'entry': entry}
        container_metadata = eval(template.render(context))
        # FIXME: Check with Rasta and replace below code with a way to update metadata
        # This corrupts the metadata of the container -
        # is the metadata update only possible for simple objects in Phaidra?

        # res = requests.post(
        #     self.uris.get('BASE_URI') + f'object/{entry.archive_id}/metadata',
        #     {'metadata': dumps(container_metadata)},
        #     auth=(self.credentials.get('USER'), self.credentials.get('PWD')),
        # )
        # return res

    def phaidra_archive(self, media):
        # Find associated entry object for this asset
        entry = Entry.objects.get(id=media.entry_id)

        # if the entry is not already archived as a container, create a container object
        if not entry.archive_id:
            res = self._phaidra_create_container(entry)
            if res.status_code != 200:
                logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
                return res

            pid = loads(res.content).get('pid', '')
            if pid.strip():
                entry.archive_URI = self.uris.get('BASE_URI') + pid
                entry.archive_id = pid
                entry.save()
        else:
            # Assume that there is a metadata change and update the container metadata
            res = self._phaidra_update_container(entry)
            return res

        if media.archive_id:
            # media already archived and linked to entry object
            # TODO: Are we really sure that in PHAIDRA
            # this media asset linked to its respective container?
            return {'pid': entry.archive_id}

        # Create a media object separately
        if media.type == IMAGE_TYPE:
            post_url = self.uris.get('PICTURE_CREATE')
        elif media.type == AUDIO_TYPE:
            post_url = self.uris.get('AUDIO_CREATE')
        elif media.type == VIDEO_TYPE:
            post_url = self.uris.get('VIDEO_CREATE')
        elif media.type == DOCUMENT_TYPE:
            post_url = self.uris.get('DOCUMENT_CREATE')
        else:
            post_url = self.uris.get('OBJECT_CREATE')

        template = loader.get_template('phaidra_member.json')
        context = {'media': media}
        member_metadata = eval(template.render(context))
        res = requests.post(
            post_url,
            files={
                'metadata': dumps(member_metadata),
                'file': media.file,
            },
            auth=(self.credentials.get('USER'), self.credentials.get('PWD')),
        )

        if res.status_code != 200:
            logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
            return res

        pid = loads(res.content).get('pid', '')
        if pid.strip():
            media.archive_URI = self.uris.get('BASE_URI') + pid
            media.archive_id = pid
            media.save()

            # Add member to container
            link_member_url = self.uris.get("BASE_URI") + f'object/{entry.archive_id}/relationship/add'

            res = requests.post(
                link_member_url,
                {'predicate': 'http://pcdm.org/models#hasMember', 'object': f'info:fedora/{media.archive_id}'},
                auth=(self.credentials.get('USER'), self.credentials.get('PWD')),
            )

            if res.status_code != 200:
                logging.warning('Response:\nStatus: %s\nContent: %s', res.status_code, res.content)
                return res

        return {'pid': entry.archive_id}
