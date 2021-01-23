import logging
from json import dumps, loads

import requests

from django.conf import settings
from django.template import loader

from core.models import Entry
from media_server.models import Media, get_media_for_entry


class Archiver:
    def __init__(self):
        self.user = settings.ARCHIVE_SETTINGS.get('USER')
        self.pwd = settings.ARCHIVE_SETTINGS.get('PWD')
        self.base_id = settings.ARCHIVE_SETTINGS.get('IDENTIFIER_BASE')
        self.create_uri = settings.ARCHIVE_SETTINGS.get('CREATE_URI')


    def archive(self, entry):
        if settings.ARCHIVE_TYPE == 'PHAIDRA':
            return self.phaidra_archive(entry)


    def phaidra_archive(self, entry):
        media = get_media_for_entry(entry.pk, flat=True)
        # print(media)
        template = loader.get_template('phaidra_container.json')

        context = {
            'entry': entry,
            'media': [Media.objects.get(id=pk) for pk in media]
        }
        # Cannot use json.loads because there is a
        # trailing comma after last element
        # generated by template rendering
        data = eval(template.render(context))
        files = {f'member_{pk}': Media.objects.get(id=pk).file for pk in media}
        # return data (for debugging only)
        res = requests.post(self.create_uri,
                            files={**files,
                                   'metadata': dumps(data)},
                            auth=(self.user, self.pwd))
        if res.status_code != 200:
            logging.warning ('Response:\nStatus: %s\nContent: %s',
                             res.status_code,
                             res.content)

        pid = loads(res.content).get('pid', '')
        if pid.strip():
            entry.archive_URI = self.base_id + pid
            entry.archive_id = pid
            entry.save()

        return res
