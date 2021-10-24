"""
https://basedev.uni-ak.ac.at/redmine/issues/1556

I was archiving a slightly bigger file (~60 MB), which took a while. During the asynchronous upload I changed the
metadata, saved the changes, but the button "View in Archive" did not change to the update metadata state.
"""
from datetime import datetime, timedelta

from rest_framework.test import APITestCase
import django_rq
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider, ClientProvider
import freezegun


class DeleteMediaJobs(APITestCase):
    def setUp(self) -> None:
        # I was archiving a slightly bigger file (~60 MB), which took a while.

        # simulate nothing happens
        from media_server.archiver.implementations.phaidra.media.archiver import MediaArchiveHandler

        MediaArchiveHandler.push_to_archive = lambda *args, **kwargs: None
        self.connection = django_rq.get_connection()

        self.model_provider = ModelProvider()
        self.client_provider = ClientProvider(self.model_provider)

        self.now = datetime(2005, 1, 1, 14, 22, 3)
        with freezegun.freeze_time(self.now):
            self.entry = self.model_provider.get_entry()
            self.media = self.model_provider.get_media(self.entry)
            self.client_provider.get_media_primary_key_response(self.media, only_validate=False)
            django_rq.get_worker().work(burst=True)  # but the entry gets archived

        # During the asynchronous upload I changed the metadata
        self.client.login(username=self.model_provider.username, password=self.model_provider.peeword)

        time_gone = timedelta(seconds=30)
        self.now += time_gone
        with freezegun.freeze_time(self.now):
            self.client.patch(
                path=f"/api/v1/entry/{self.entry.id}/",
                data={'title': 'New Title'}
            )

    def test_archive_is_not_up_to_date(self):
        # but the button "View in Archive" did not change to the update metadata state.
        response = self.client.get(
            path=f"/api/v1/archive/is-changed?entry={self.entry.id}",
        )

        self.assertEqual(response.content, b'true')
