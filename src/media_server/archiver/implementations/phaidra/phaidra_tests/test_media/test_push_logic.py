from typing import TYPE_CHECKING, Optional

import django_rq

from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.implementations.phaidra.media.archiver import MediaArchiver, _push_to_archive_job
from media_server.archiver.interface.responses import SuccessfulArchiveResponse

if TYPE_CHECKING:
    from core.models import Entry

from django.test import TestCase

from media_server.archiver.implementations.phaidra.metadata.archiver import DefaultMetadataArchiver
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider
from media_server.archiver.interface.archiveobject import ArchiveObject


class MediaArchivalInternalLogicTestCase(TestCase):
    """Test if media of an entry can be uploaded."""

    entry: Optional['Entry'] = None
    model_provider: Optional['ModelProvider'] = None
    archive_object: Optional['ArchiveObject'] = None

    def setUp(self):
        """
        We need one entry, that has been archived yet
        :return:
        """
        self.model_provider = ModelProvider()
        self.entry = self.model_provider.get_entry(thesis_type=False)
        self.archive_object = ArchiveObject(
            entry=self.entry,
            media_objects=set(),  # nothing to here, since we test this,
            user=self.model_provider.user,
        )
        archiver = DefaultMetadataArchiver(self.archive_object)
        archiver.push_to_archive()
        self.media = self.model_provider.get_media(self.entry)
        self.archive_object.media_objects.add(self.media)

    def test_sync(self):
        """
        In the code
        :return:
        """
        archiver = MediaArchiver(self.archive_object)
        response = archiver.push_to_archive()
        self.assertIsInstance(response, SuccessfulArchiveResponse)
        self.assertEqual(response.data['object'], f'Media <{self.media.archive_id}>')

    def test_async(self):
        """
        `media_server.archiver.controller.asyncmedia.AsyncMediaHandler.enqueue`
        :return:
        """
        async_media_handler = AsyncMediaHandler(self.archive_object.media_objects, _push_to_archive_job)
        async_media_handler.enqueue()
        worker = django_rq.get_worker(async_media_handler.queue_name)
        worker.work(burst=True)  # wait until it is done
        media = self.archive_object.media_objects.pop()
        media.refresh_from_db()
        self.assertRegex(media.archive_id, r'o:\d+')
