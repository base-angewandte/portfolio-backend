from typing import TYPE_CHECKING, Optional

import django_rq
import requests

from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.implementations.phaidra.media.archiver import MediaArchiver, _push_to_archive_job
from media_server.archiver.interface.responses import SuccessfulArchiveResponse

if TYPE_CHECKING:
    from core.models import Entry

from django.test import TestCase

from media_server.archiver.implementations.phaidra.metadata.archiver import DefaultMetadataArchiver
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ClientProvider, ModelProvider
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


class MediaArchivalEndpointLogicTestCase(TestCase):
    def setUp(self) -> None:
        self.model_provider = ModelProvider()
        self.entry = self.model_provider.get_entry(thesis_type=False)
        self.media = self.model_provider.get_media(entry=self.entry)
        self.client_provider = ClientProvider(self.model_provider)

    def test_media_archival_db(self):
        self.client_provider.get_media_primary_key_response(self.media, only_validate=False)
        # make sure it is done
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)
        self.media.refresh_from_db()
        self.assertRegex(self.media.archive_id, r'o:\d+')

    def test_media_archival_phaidra(self):
        response = self.client_provider.get_media_primary_key_response(self.media, only_validate=False)
        if response.status_code != 200:
            raise RuntimeError(f'{response.status_code=} {response.json()=}')
        # make sure it is done
        worker = django_rq.get_worker(AsyncMediaHandler.queue_name)
        worker.work(burst=True)
        self.media.refresh_from_db()
        phaidra_response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media.archive_id}/index'
        )

        self.assertEqual(phaidra_response.status_code, 200)
