import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import django_rq
from freezegun import freeze_time

from django.test import TestCase

from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.controller.status_info import EntryArchivalInformer
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ClientProvider, ModelProvider

if TYPE_CHECKING:
    from django.http import HttpResponse


class EntryNoMediaNotArchivedTestCase(TestCase):
    """An Entry with no media.

    None not archived
    """

    entry_archival_informer: 'EntryArchivalInformer'
    response: 'HttpResponse'

    @classmethod
    def setUpTestData(cls):
        """
        Create the entry and get a response from the api
        :return:
        """
        model_provider = ModelProvider()
        entry = model_provider.get_entry()
        cls.entry_archival_informer = EntryArchivalInformer(entry)
        cls.response = ClientProvider(model_provider).get_is_changed_response(entry)

    def test_entry_data(self):
        self.assertIsNone(self.entry_archival_informer.data.entry.changed_since_archival)
        self.assertEqual(0, self.entry_archival_informer.data.assets.__len__())

    def test_entry_calculation(self):
        self.assertIsNone(self.entry_archival_informer.has_changed)

    def test_response(self):
        self.assertIsNone(json.loads(self.response.content.decode('utf-8')))


class EntryWithMediaArchived(TestCase):
    """An entry with media.

    Both archived
    """

    entry_archival_informer: 'EntryArchivalInformer'
    response: 'HttpResponse'

    @classmethod
    def setUpTestData(cls):
        """
        Create the entry and the media, archive media and get a response from the api
        :return:
        """
        model_provider = ModelProvider()
        entry = model_provider.get_entry()
        media = model_provider.get_media(entry)
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(media, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        entry.refresh_from_db()
        cls.entry_archival_informer = EntryArchivalInformer(entry)
        cls.response = client_provider.get_is_changed_response(entry)

    def test_entry_data(self):
        self.assertFalse(self.entry_archival_informer.data.entry.changed_since_archival)
        self.assertEqual(1, self.entry_archival_informer.data.assets.__len__())
        self.assertFalse(self.entry_archival_informer.data.assets[0].changed_since_archival)

    def test_entry_calculation(self):
        self.assertFalse(self.entry_archival_informer.has_changed)

    def test_response(self):
        self.assertFalse(json.loads(self.response.content.decode('utf-8')))


class EntryWithMediaSavedAfterArchival(TestCase):
    """An entry with media.

    The media is saved after archival.
    """

    entry_archival_informer: 'EntryArchivalInformer'
    response: 'HttpResponse'

    @classmethod
    def setUpTestData(cls):
        """
        Create the entry and the media, archive media, update the media and get a response from the api
        :return:
        """
        # Create 1. Timeline
        cls.timedelta_between_steps = timedelta(seconds=60)
        cls.time_of_entry_creation = datetime(2021, 1, 1, 0, 0)
        cls.time_of_media_creation = cls.time_of_entry_creation + cls.timedelta_between_steps
        cls.time_of_archival = cls.time_of_media_creation + cls.timedelta_between_steps
        cls.time_of_media_update = cls.time_of_archival + cls.timedelta_between_steps
        cls.time_of_check_if_up_to_date = cls.time_of_media_update + cls.timedelta_between_steps

        model_provider = ModelProvider()
        client_provider = ClientProvider(model_provider)

        with freeze_time(cls.time_of_entry_creation):
            entry = model_provider.get_entry()
        with freeze_time(cls.time_of_media_creation):
            media = model_provider.get_media(entry)
        with freeze_time(cls.time_of_archival):
            client_provider.get_media_primary_key_response(media, only_validate=False)
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done
            entry.refresh_from_db()
            media.refresh_from_db()
        with freeze_time(cls.time_of_media_update):
            media.license = {
                'label': {'de': 'urheberrechtlich geschützt', 'en': 'Copyright'},
                'source': 'http://base.uni-ak.ac.at/portfolio/licenses/copyright',
            }
            media.save(update_fields=['license', 'modified'])
            media.refresh_from_db()
        with freeze_time(cls.time_of_check_if_up_to_date):
            threshold = int(cls.timedelta_between_steps.total_seconds() // 2)
            cls.entry_archival_informer = EntryArchivalInformer(entry, threshold, threshold)
            cls.response = client_provider.get_is_changed_response(entry, threshold, threshold)

    def test_entry_data(self):
        self.assertFalse(self.entry_archival_informer.data.entry.changed_since_archival)
        self.assertEqual(1, self.entry_archival_informer.data.assets.__len__())
        self.assertTrue(self.entry_archival_informer.data.assets[0].changed_since_archival)

    def test_entry_calculation(self):
        self.assertTrue(self.entry_archival_informer.has_changed)

    def test_response(self):
        self.assertTrue(json.loads(self.response.content.decode('utf-8')))


class EntrySavedAfterArchivalMediaUpToDate(TestCase):
    """An Entry, that is saved after archival, the media is up to date."""

    entry_archival_informer: 'EntryArchivalInformer'
    response: 'HttpResponse'

    @classmethod
    def setUpTestData(cls):
        """
        Create the entry and the media, archive media, update the entry and get a response from the api
        :return:
        """
        model_provider = ModelProvider()
        client_provider = ClientProvider(model_provider)

        cls.timedelta_between_steps = timedelta(seconds=60)
        cls.creation_time = datetime(2021, 1, 1, 0, 0)
        cls.archival_time = cls.creation_time + cls.timedelta_between_steps
        cls.update_time = cls.archival_time + cls.timedelta_between_steps
        cls.check_if_changed_time = cls.update_time + cls.timedelta_between_steps

        with freeze_time(cls.creation_time):
            entry = model_provider.get_entry()
            media = model_provider.get_media(entry)
        with freeze_time(cls.archival_time):
            client_provider.get_media_primary_key_response(media, only_validate=False)
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done
        with freeze_time(cls.update_time):
            entry.title += ' more words'
            entry.save(update_fields=['title', 'date_changed'])
            entry.refresh_from_db()
        with freeze_time(cls.check_if_changed_time):
            threshold = int(cls.timedelta_between_steps.total_seconds() // 2)
            cls.entry_archival_informer = EntryArchivalInformer(entry, threshold, threshold)
            cls.response = client_provider.get_is_changed_response(entry, threshold, threshold)

    def test_entry_data(self):
        self.assertTrue(self.entry_archival_informer.data.entry.changed_since_archival)
        self.assertEqual(1, self.entry_archival_informer.data.assets.__len__())
        self.assertFalse(self.entry_archival_informer.data.assets[0].changed_since_archival)

    def test_entry_calculation(self):
        self.assertTrue(self.entry_archival_informer.has_changed)

    def test_response(self):
        self.assertTrue(json.loads(self.response.content.decode('utf-8')))


class EntryUpToDateMediaMixed(TestCase):
    """En entry, that has one media file, which is up-to-date and one, which is
    out of sync."""

    entry_archival_informer: 'EntryArchivalInformer'
    response: 'HttpResponse'

    @classmethod
    def setUpTestData(cls):
        """
        Create the entry and two assets, archive assets, update one asset and get a response from the api
        :return:
        """
        model_provider = ModelProvider()
        client_provider = ClientProvider(model_provider)

        cls.timedelta_between_steps = timedelta(seconds=60)
        cls.creation_time = datetime(2021, 4, 1, 11, 11)
        cls.archival_time = cls.creation_time + cls.timedelta_between_steps
        cls.update_time = cls.archival_time + cls.timedelta_between_steps
        cls.look_up_time = cls.update_time + cls.timedelta_between_steps

        with freeze_time(cls.creation_time):
            entry = model_provider.get_entry()
            media_in_sync = model_provider.get_media(entry)
            media_out_of_sync = model_provider.get_media(entry)

        with freeze_time(cls.archival_time):
            client_provider.get_media_primary_key_response(media_in_sync, only_validate=False)
            client_provider.get_media_primary_key_response(media_out_of_sync, only_validate=False)
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done

        with freeze_time(cls.update_time):
            media_out_of_sync.license = {
                'label': {'de': 'urheberrechtlich geschützt', 'en': 'Copyright'},
                'source': 'http://base.uni-ak.ac.at/portfolio/licenses/copyright',
            }
            media_out_of_sync.save(update_fields=['license', 'modified'])

        with freeze_time(cls.look_up_time):
            entry.refresh_from_db()
            threshold = int(cls.timedelta_between_steps.total_seconds() / 2)
            cls.entry_archival_informer = EntryArchivalInformer(entry, threshold, threshold)
            cls.response = client_provider.get_is_changed_response(entry, threshold, threshold)

    def test_entry_data(self):
        self.assertFalse(self.entry_archival_informer.data.entry.changed_since_archival)
        self.assertEqual(2, self.entry_archival_informer.data.assets.__len__())
        self.assertEqual(
            {True, False},
            {asset_info.changed_since_archival for asset_info in self.entry_archival_informer.data.assets},
        )

    def test_entry_calculation(self):
        self.assertTrue(self.entry_archival_informer.has_changed)

    def test_response(self):
        self.assertTrue(json.loads(self.response.content.decode('utf-8')))
