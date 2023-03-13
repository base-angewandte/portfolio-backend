"""The time of archival of entries and media should be logged in the
database."""
from datetime import date, timedelta
from typing import Optional

from freezegun import freeze_time

import django_rq

from django.test import TestCase
from django.utils import timezone

from core.models import Entry
from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ClientProvider, ModelProvider
from media_server.archiver.utilities import DateTimeComparator
from media_server.models import Media


class NotArchivedTestCase(TestCase):
    """An not archived entry / media pair should not have archival dates."""

    entry: Optional[Entry] = None
    media: Optional[Media] = None

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

    entry: Optional[Entry] = None
    media: Optional[Media] = None

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
        response = client_provider.get_media_primary_key_response(cls.media, only_validate=False)
        if response.status_code != 200:
            raise RuntimeError(f'Could not archive test asset due to <{response.content}>')
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)  # wait until it is done
        cls.entry.refresh_from_db()
        cls.media.refresh_from_db()

    def test_entry_archival_date(self):
        self.assertIsNotNone(self.entry.archive_date)
        self.assertIsInstance(self.entry.archive_date, date)
        self.assertEqual(self.entry.archive_date, self.entry.date_changed)

    def test_media_has_archival_date(self):
        self.assertIsNotNone(self.media.archive_date)
        self.assertIsInstance(self.media.archive_date, date)
        self.assertGreater(self.media.archive_date, self.media.modified)


class SavedAfterArchivalTestCase(TestCase):
    """An archived entry / media pair that is saved again after archival,
    should have newer save than archival dates."""

    entry: Optional[Entry] = None
    media: Optional[Media] = None
    time_gone: int = 1

    @classmethod
    def setUpTestData(cls):
        """
        Create an entry with one media, archive both and save them
        :return:
        """
        now = timezone.now() - timedelta(days=5)
        with freeze_time(now):
            model_provider = ModelProvider()
            cls.entry = model_provider.get_entry()
            cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
            client_provider = ClientProvider(model_provider)
            cls.media_push_response = client_provider.get_media_primary_key_response(cls.media, only_validate=False)
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done
        time_gone = timedelta(seconds=cls.time_gone)
        with freeze_time(now + time_gone):
            cls.entry.refresh_from_db()
            cls.media.refresh_from_db()
            cls.entry.title += ' changed!'  # just to change anything. I am not sure, if it is saved, if not
            cls.entry.save()
            cls.entry.refresh_from_db()
            cls.media.published = not cls.media.published  # just to change anything
            cls.media.save()
            cls.media.refresh_from_db()

    def test_entry_archival_date_differs_from_save_date(self):
        self.assertGreater(
                self.entry.date_changed,
                self.entry.archive_date,
        )

    def test_media_archival_date_differs_from_save_date(self):
        self.assertGreater(
                self.media.modified,
                self.media.archive_date,
            )


class UpdatedArchivalTestCase(TestCase):
    """An archived entry / media pair, that is saved, archived, updated, and
    updated the archival as well, should have the same save and archival
    dates."""

    entry: Optional[Entry] = None
    media: Optional[Media] = None
    time_gone: int = 1

    @classmethod
    def setUpTestData(cls):
        """Create an entry with one media, archive both, save them and update
        the archive.

        :return:
        """
        now = timezone.now() - timedelta(days=5)
        with freeze_time(now):
            model_provider = ModelProvider()
            cls.entry = model_provider.get_entry()
            cls.media = model_provider.get_media(entry=cls.entry, file_type='pdf', mime_type='application/pdf')
            client_provider = ClientProvider(model_provider)
            response = client_provider.get_media_primary_key_response(cls.media, only_validate=False)
            if response.status_code != 200:
                raise RuntimeError(f'Could not archive test asset due to <{response.content}>')
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done
        with freeze_time(now + timedelta(seconds=cls.time_gone)):
            cls.entry.refresh_from_db()
            cls.media.refresh_from_db()
            cls.entry.title += ' changed!'  # just to change anything. I am not sure, if it is saved, if not
            cls.entry.save()
            # just to change anything. I am not sure, if it is saved, if not
            cls.media.license = {
                'label': {'de': 'urheberrechtlich geschützt', 'en': 'Copyright'},
                'source': 'http://base.uni-ak.ac.at/portfolio/licenses/copyright',
            }
            cls.media.save()
            response = client_provider.get_update_entry_archival_response(cls.entry)
            if response.status_code != 200:
                raise RuntimeError(
                    f'Update call returned '
                    f'response.status_code={response.status_code} '
                    f'and response.content={response.content}')
            worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
            worker.work(burst=True)  # wait until it is done
            cls.entry.refresh_from_db()
            cls.media.refresh_from_db()

    def test_entry_archival_and_save_date_are_the_same(self):
        self.assertTrue(
            DateTimeComparator(max_seconds=self.time_gone).about_the_same(
                self.entry.archive_date, self.entry.date_changed
            ),
            f"""self.entry.archive_date={self.entry.archive_date}
self.entry.date_changed={self.entry.date_changed}
{(self.entry.archive_date - self.entry.date_changed).total_seconds()}""",
        )

    def test_media_archival_and_save_date_are_the_same(self):
        self.assertTrue(
            DateTimeComparator(self.time_gone).about_the_same(self.media.archive_date, self.media.modified),
            f'\nself.media.archive_date={self.media.archive_date}\n'
            f'self.media.modified={self.media.modified}',
        )
