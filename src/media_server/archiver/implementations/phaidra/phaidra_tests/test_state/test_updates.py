from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import django_rq
from freezegun import freeze_time

from django.test import TestCase
from django.utils import timezone

from media_server.archiver import STATUS_ARCHIVED
from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.controller.status_info import EntryArchivalInformer
from media_server.archiver.implementations.phaidra.phaidra_tests.utilities import ClientProvider, ModelProvider

if TYPE_CHECKING:
    from rest_framework.response import Response

    from core.models import Entry
    from media_server.models import Media


class EntryWithMediaSaveAfterArchival(TestCase):
    """An entry with media.

    The media is saved after archival.
    """

    entry_archival_informer: 'EntryArchivalInformer'
    response: 'Response'
    time_of_entry_creation: datetime
    timedelta_between_steps: timedelta
    time_of_media_creation: datetime
    time_of_archival: datetime
    time_of_media_update: datetime
    time_of_archive_update: datetime
    entry: 'Entry'
    media: 'Media'

    @classmethod
    def setUpTestData(cls):
        """
        Create the entry and the media, archive media, update the media and get a response from the api
        :return:
        """
        # Create 1. Timeline
        cls.timedelta_between_steps = timedelta(seconds=60)
        cls.time_of_entry_creation = timezone.now() - timedelta(days=5)
        cls.time_of_media_creation = cls.time_of_entry_creation + cls.timedelta_between_steps
        cls.time_of_archival = cls.time_of_media_creation + cls.timedelta_between_steps
        cls.time_of_media_update = cls.time_of_archival + cls.timedelta_between_steps
        cls.time_of_archive_update = cls.time_of_media_update + cls.timedelta_between_steps

        model_provider = ModelProvider()
        client_provider = ClientProvider(model_provider)

        with freeze_time(cls.time_of_entry_creation):
            cls.entry = model_provider.get_entry()
        with freeze_time(cls.time_of_media_creation):
            cls.media = model_provider.get_media(cls.entry)
        with freeze_time(cls.time_of_archival):
            client_provider.get_media_primary_key_response(cls.media, only_validate=False)
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done
            cls.entry.refresh_from_db()
            cls.media.refresh_from_db()
        with freeze_time(cls.time_of_media_update):
            cls.media.license = {
                'label': {'de': 'urheberrechtlich geschützt', 'en': 'Copyright'},
                'source': 'http://base.uni-ak.ac.at/portfolio/licenses/copyright',
            }
            cls.media.save(update_fields=['license', 'modified'])
            cls.media.refresh_from_db()
        with freeze_time(cls.time_of_archive_update):
            cls.entry.refresh_from_db()
            client_provider.get_update_entry_archival_response(entry=cls.entry)
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done

        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()

    def test_media_archive_status(self):
        self.assertEqual(self.media.archive_status, STATUS_ARCHIVED)

    def test_media_archive_time(self):
        self.assertEqual(self.media.archive_date, self.time_of_archive_update)
