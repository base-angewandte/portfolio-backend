from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum

import requests
from typing import Optional, Union, Callable, Dict

import django_rq
from rq.job import Job
from freezegun import freeze_time
from rest_framework.test import APITestCase

from media_server.archiver.choices import STATUS_NOT_ARCHIVED, STATUS_TO_BE_ARCHIVED, STATUS_ARCHIVED
from media_server.archiver.controller.asyncmedia import AsyncMediaHandler
from media_server.archiver.implementations.phaidra.phaidra_tests.utillities import ModelProvider, ClientProvider

# Utilities
from media_server.models import Media


@dataclass
class MediaDataState:
    """
    Snapshot of a media object, that contains important features to check correct state.
    """
    time_of_action: datetime
    """"""
    modified: datetime
    """Media.modified"""
    archive_date: Optional[datetime] = None
    """Media.archive_date"""
    archive_status: Optional[int] = STATUS_NOT_ARCHIVED
    """Media.archive_status"""
    license: Optional[dict] = None
    """Media.license"""
    license_in_archive: Optional[Union[dict, list]] = None
    """How the license appears in the archive"""
    archive_is_changed: Optional[bool] = None
    """route archive/is-changed"""


# Some variables we need
context_time = datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc)
media_date_created = context_time + timedelta(hours=1)  # datetime(2000, 1, 1, 1, 0, 0, 0, tzinfo=<UTC>)
media_date_archived = context_time + timedelta(hours=2)  # datetime(2000, 1, 1, 2, 0, 0, 0, tzinfo=<UTC>)
media_date_modified = context_time + timedelta(hours=3)  # datetime(2000, 1, 1, 3, 0, 0, 0, tzinfo=<UTC>)
media_date_schedule_processing = context_time + timedelta(hours=4)  # datetime(2000, 1, 1, 4, 0, 0, 0, tzinfo=<UTC>)
media_date_processed = context_time + timedelta(hours=5)  # datetime(2000, 1, 1, 5, 0, 0, 0, tzinfo=<UTC>)


license_cc_portfolio = {
    'label': {'en': 'Creative Commons Attribution 4.0'},
    'source': 'http://base.uni-ak.ac.at/portfolio/licenses/CC-BY-4.0',
}

license_dd_portfolio = {
    'source': 'http://base.uni-ak.ac.at/portfolio/licenses/copyright',
    'label': {'de': 'urheberrechtlich geschützt', 'en': 'Copyright'}
}

license_cc_phaidra = ["http://creativecommons.org/licenses/by/4.0/", ]


class MediaDataStateName(Enum):
    CREATED = 'created'
    REQUESTED_ARCHIVAL = 'requested_archival'
    CHANGED_LICENSE = 'changed_license'
    SUCCESSFUL_ASYNC_OPERATIONS = 'successful_async_operations'


order_of_states = [MediaDataStateName.CREATED, MediaDataStateName.REQUESTED_ARCHIVAL,
                   MediaDataStateName.CHANGED_LICENSE, MediaDataStateName.SUCCESSFUL_ASYNC_OPERATIONS]

"""Some states to test with name: state"""
media_data_states: Dict[MediaDataStateName, MediaDataState] = {
    MediaDataStateName.CREATED: MediaDataState(
        time_of_action=media_date_created,
        modified=media_date_created,
        archive_date=None,
        archive_status=STATUS_NOT_ARCHIVED,
        license=license_cc_portfolio,
        license_in_archive=None,
        archive_is_changed=None,
    ), MediaDataStateName.REQUESTED_ARCHIVAL: MediaDataState(
        time_of_action=media_date_archived,
        modified=media_date_archived,
        archive_date=None,
        archive_status=STATUS_TO_BE_ARCHIVED,
        license=license_cc_portfolio,
        license_in_archive=None,
        archive_is_changed=False,
    ), MediaDataStateName.CHANGED_LICENSE: MediaDataState(
        time_of_action=media_date_modified,
        modified=media_date_modified,
        archive_date=None,
        archive_status=STATUS_TO_BE_ARCHIVED,
        license=license_dd_portfolio,
        license_in_archive=None,
        archive_is_changed=True,
    ), MediaDataStateName.SUCCESSFUL_ASYNC_OPERATIONS: MediaDataState(
        time_of_action=media_date_processed,
        modified=media_date_modified,
        archive_date=media_date_archived,
        archive_status=STATUS_ARCHIVED,
        license=license_dd_portfolio,
        license_in_archive=license_cc_phaidra,
        archive_is_changed=True,
    )}


# The user has created the media object. It is not yet converted or archived
# The user requests archival, no conversion has happened yet

# The user decides to change the license, no archival or conversion has happened yet

# Conversion and archival finally happened


# Some functions to create this states for testing


def set_time_frame(time_of_action: datetime) -> Callable:
    def _contextualize(function: Callable) -> Callable:
        def _wrapper(self_: 'StateManager', media: Optional['Media'] = None) -> 'Media':
            if media is not None:
                media.refresh_from_db()
            with freeze_time(time_of_action):
                media = function(self_, media)
            if media is None:
                raise RuntimeError(f'function {function} did not return a Media object')
            media.refresh_from_db()
            return media

        return _wrapper

    return _contextualize


class StateManager:
    state: Optional[MediaDataStateName] = None

    @dataclass
    class DataStateCreatorPair:
        name: MediaDataStateName
        state: MediaDataState
        create_function: Callable[[Optional[Media]], Media]

    def __init__(self):
        with freeze_time(context_time):
            AsyncMediaHandler.run_at = media_date_schedule_processing
            self.queue = django_rq.get_queue()
            self.model_provider = ModelProvider()
            self.client_provider = ClientProvider(self.model_provider)

        self.state = None
        self.media_data_states_creation_pairs = (
            self.DataStateCreatorPair(MediaDataStateName.CREATED, media_data_states[MediaDataStateName.CREATED],
                                      self.create_media),
            self.DataStateCreatorPair(MediaDataStateName.REQUESTED_ARCHIVAL,
                                      media_data_states[MediaDataStateName.REQUESTED_ARCHIVAL],
                                      self.request_media_archival),
            self.DataStateCreatorPair(MediaDataStateName.CHANGED_LICENSE,
                                      media_data_states[MediaDataStateName.CHANGED_LICENSE],
                                      self.change_license),
            self.DataStateCreatorPair(MediaDataStateName.SUCCESSFUL_ASYNC_OPERATIONS,
                                      media_data_states[MediaDataStateName.SUCCESSFUL_ASYNC_OPERATIONS],
                                      self.successful_async_operations),
        )

    def clean_up(self) -> None:
        AsyncMediaHandler.run_at = None
        self.model_provider.user.delete()

    @set_time_frame(media_data_states[MediaDataStateName.CREATED].time_of_action)
    def create_media(self, _=None) -> Media:
        """
        Create media for state "created"
        :param _: Placeholder for argument media, which will be called in other functions
        :return:
        """
        entry = self.model_provider.get_entry()
        return self.model_provider.get_media(entry)

    @set_time_frame(media_data_states[MediaDataStateName.REQUESTED_ARCHIVAL].time_of_action)
    def request_media_archival(self, media: Media) -> Media:
        """
        Modify media for state "requested_archival"
        :param media:
        :return:
        """
        response = self.client_provider.get_media_primary_key_response(media, False)
        if response.status_code != 200:
            raise RuntimeError(f'Response status code is {response.status_code} with content {response.data}')
        return media

    @set_time_frame(media_data_states[MediaDataStateName.CHANGED_LICENSE].time_of_action)
    def change_license(self, media: Media) -> Media:
        """
        Modify media for state "changed_license"
        :param media:
        :return:
        """
        media.license = media_data_states[MediaDataStateName.CHANGED_LICENSE].license
        media.save()
        return media

    @set_time_frame(media_data_states[MediaDataStateName.SUCCESSFUL_ASYNC_OPERATIONS].time_of_action)
    def successful_async_operations(self, media: Media) -> Media:
        """
        Modify media for state "successful_async_operations"
        :param media:
        :return:
        """
        # The time frames with freeze gun and redis do not work good enough. So manually requeue the job
        job = Job.fetch(media.get_archive_job_id(), self.queue.connection)
        job.delete()
        self.queue.enqueue(job.func, job.args[0], job_id=job.id, failure_ttl=job.failure_ttl)
        django_rq.get_worker(AsyncMediaHandler.queue_name).work(burst=True)
        return media

    def run_operations_until_state(self, final_state: MediaDataStateName) -> Media:
        """
        Utility function to set states with string
        :param final_state:
        :return:
        """
        if final_state not in media_data_states:
            raise KeyError(f'{final_state} is not a defined states in media_data_states: {media_data_states.keys()}')
        if self.state is not None:
            raise NotImplementedError('Currently you have to start at a clean state')
        media = None
        for media_data_states_creation_pair in self.media_data_states_creation_pairs:
            media = media_data_states_creation_pair.create_function(media)
            self.state = media_data_states_creation_pair.name
            if media_data_states_creation_pair.name == final_state:
                break
        return media


# Tests

class MediaCreatedTestCase(APITestCase):
    TARGET_STATUS = MediaDataStateName.CREATED
    media: Media
    desired_data_status: MediaDataState
    state_manager: StateManager

    @classmethod
    def setUpTestData(cls):
        cls.desired_data_status = media_data_states[cls.TARGET_STATUS]
        cls.state_manager = StateManager()
        cls.media = cls.state_manager.run_operations_until_state(cls.TARGET_STATUS)

    @classmethod
    def tearDownClass(cls):
        cls.state_manager.clean_up()
        super().tearDownClass()

    def test_media_modified_date(self):
        self.assertEqual(self.media.modified, self.desired_data_status.modified)

    def test_media_archive_state(self):
        self.assertEqual(self.media.archive_status, self.desired_data_status.archive_status)

    def test_media_archive_date(self):
        self.assertEqual(self.media.archive_date, self.desired_data_status.archive_date)

    def test_media_license(self):
        self.assertEqual(self.media.license, self.desired_data_status.license)

    def test_archive_is_changed(self):
        self.client.login(
            username=self.state_manager.model_provider.username,
            password=self.state_manager.model_provider.peeword
        )
        response = self.client.get(
            f'/api/v1/archive/is-changed?entry={self.media.entry_id}', content_type='application/json'
        )
        if response.status_code != 200:
            raise RuntimeError(f'Response code {response.status_code} with contend {response.body}')
        self.assertEqual(response.json(), self.desired_data_status.archive_is_changed)


class MediaRequestedArchivalTestCase(MediaCreatedTestCase):
    TARGET_STATUS = MediaDataStateName.REQUESTED_ARCHIVAL


class MediaChangedLicenseTestCase(MediaCreatedTestCase):
    TARGET_STATUS = MediaDataStateName.CHANGED_LICENSE


class MediaSuccessfulAsyncOperationsTestCase(MediaCreatedTestCase):
    TARGET_STATUS = MediaDataStateName.SUCCESSFUL_ASYNC_OPERATIONS

    def test_phaidra_license(self):
        if not self.media.archive_id:
            raise RuntimeError('Media does not have an archive id. This test can not work.')
        response = requests.get(
            f'https://services.phaidra-sandbox.univie.ac.at/api/object/{self.media.archive_id}/jsonld'
        )
        if response.status_code != 200:
            raise RuntimeError(
                f'Phaidra server did respond with status code {response.status_code} and contend {response.text}'
            )
        self.assertEqual(
            response.json()['edm:rights'],
            self.desired_data_status.license_in_archive
        )
