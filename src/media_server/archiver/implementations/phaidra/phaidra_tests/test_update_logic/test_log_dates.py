"""The time of archival of entries and media should be logged in the
database."""
from datetime import date
from time import sleep

import django_rq

from django.test import TestCase

from core.models import Entry
from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ClientProvider, ModelProvider
from media_server.archiver.utilities import DateTimeComparator
from media_server.models import Media


class NotArchivedTestCase(TestCase):
    """An not archived entry / media pair should not have archival dates."""

    media: Media
    entry: Entry

    @classmethod
    def setUpTestData(cls):
        """
        Create an entry with one media
        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()
        cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')

    def test_entry_has_no_archival_date(self):
        self.assertIsNone(self.entry.archive_date)

    def test_media_has_no_archival_date(self):
        self.assertIsNone(self.media.archive_date)


class ArchivedTestCase(TestCase):
    """An archived entry / media pair should have archival dates."""

    @classmethod
    def setUpTestData(cls):
        """
        Create an entry with one media and archive both
        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()
        cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()

    def test_entry_archival_date(self):
        self.assertIsNotNone(self.entry.archive_date)
        self.assertIsInstance(self.entry.archive_date, date)
        self.assertTrue(DateTimeComparator().about_the_same(self.entry.archive_date, self.entry.date_changed))

    def test_media_has_archival_date(self):
        self.assertIsNotNone(self.media.archive_date)
        self.assertIsInstance(self.media.archive_date, date)
        self.assertTrue(DateTimeComparator().about_the_same(self.media.archive_date, self.media.modified))


class SavedAfterArchivalTestCase(TestCase):
    """An archived entry / media pair that is saved again after archival,
    should have newer save than archival dates."""

    @classmethod
    def setUpTestData(cls):
        """
        Create an entry with one media, archive both and save them
        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()
        cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.time_gone = 1
        sleep(cls.time_gone)  # currently I do not see any other way, to test this. Field is not editable
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()
        cls.entry.title += ' changed!'  # just to change anything. I am not sure, if it is saved, if not
        cls.entry.save()
        cls.entry.refresh_from_db()
        cls.media.published = not cls.media.published  # just to change anything. I am not sure, if it is saved, if not
        cls.media.save()
        cls.media.refresh_from_db()

    def test_entry_archival_date_differs_from_save_date(self):
        date_time_comparator = DateTimeComparator(max_seconds=self.time_gone)
        self.assertTrue(
            date_time_comparator.greater_then(
                self.entry.date_changed,
                self.entry.archive_date,
            ),
            f''''Entry save date is not at least {date_time_comparator.max_seconds} seconds away from archive date
{self.entry.date_changed=}
{self.entry.archive_date=}
{(self.entry.date_changed - self.entry.archive_date).total_seconds()}
''',
        )

    def test_media_archival_date_differs_from_save_date(self):
        date_time_comparator = DateTimeComparator(max_seconds=self.time_gone)
        self.assertTrue(
            date_time_comparator.greater_then(
                self.media.modified,
                self.media.archive_date,
            ),
            f''''Media save date is not at least {date_time_comparator.max_seconds} seconds away from archive date
{self.media.modified=}
{self.media.archive_date=}
{(self.media.modified - self.media.archive_date).total_seconds()}
''',
        )


class UpdatedArchivalTestCase(TestCase):
    """An archived entry / media pair, that is saved, archived, updated, and
    updated the archival as well, should have the same save and archival
    dates."""

    @classmethod
    def setUpTestData(cls):
        """Create an entry with one media, archive both, save them and update
        the archive.

        :return:
        """
        model_provider = ModelProvider()
        cls.entry = model_provider.get_entry()
        cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
        client_provider = ClientProvider(model_provider)
        client_provider.get_media_primary_key_response(cls.media, only_validate=False)
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()
        cls.entry.title += ' changed!'  # just to change anything. I am not sure, if it is saved, if not
        cls.entry.save()
        cls.media.published = not cls.media.published  # just to change anything. I am not sure, if it is saved, if not
        cls.media.save()
        client_provider.get_update_entry_archival_response(cls.entry)
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()

    def test_entry_archival_and_save_date_are_the_same(self):
        self.assertTrue(DateTimeComparator().about_the_same(self.entry.archive_date, self.entry.date_changed))

    def test_media_archival_and_save_date_are_the_same(self):
        self.assertTrue(DateTimeComparator().about_the_same(self.media.archive_date, self.media.modified))
