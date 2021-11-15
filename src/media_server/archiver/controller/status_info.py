from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional

from media_server.archiver.choices import STATUS_ARCHIVED, \
    STATUS_ARCHIVE_IN_UPDATE, STATUS_TO_BE_ARCHIVED, STATUS_ARCHIVE_IN_PROGRESS
from media_server.archiver.implementations.phaidra.media.archiver import MediaArchiver
from media_server.models import Media
from rq.job import Job
import django_rq

if TYPE_CHECKING:
    from datetime import datetime

    from core.models import Entry


@dataclass
class ItemArchivalStatus:
    id: str
    last_modify_date: 'datetime'
    archive_id: Optional[str] = None
    last_archival_date: Optional['datetime'] = None
    changed_since_archival: Optional[bool] = None


@dataclass
class EntryArchivalStatus:
    entry: 'ItemArchivalStatus'
    assets: List['ItemArchivalStatus']


class EntryArchivalInformer:
    entry: 'Entry'

    def __init__(self, entry: 'Entry'):
        """
        :param entry:
        """
        self.entry = entry

    @property
    def data(self) -> 'EntryArchivalStatus':
        asset_data = self.get_asset_data()
        redis_data = self.get_redis_data()
        return EntryArchivalStatus(
            entry=ItemArchivalStatus(
                id=self.entry.id,
                last_modify_date=self.entry.date_changed,
                archive_id=self.entry.archive_id,
                last_archival_date=self.entry.archive_date,
                changed_since_archival=self.has_entry_changed(),
            ),
            assets=asset_data + redis_data,
        )

    @property
    def has_changed(self) -> Optional[bool]:

        entry_changed = self.has_entry_changed()
        # No need for the database call for media, since one True is enough
        if entry_changed is True:
            return True
        # if entry changed is null, it is not archived, and therefore no need to look up media in the db
        if entry_changed is None:
            return None
        if entry_changed is False:
            pass  # Just to be explicit :-)

        asset_data = self.get_asset_data()
        # reduce
        asset_data = {asset_datum.changed_since_archival for asset_datum in asset_data}

        # Only check redis, if db did not already confirm changed
        if True not in asset_data:
            redis_data = self.get_redis_data()
            asset_data.update({redis_datum.changed_since_archival for redis_datum in redis_data})

        # Any changed value makes the whole thing changed
        if True in asset_data:
            return True

        # Also check in the redis

        # if {False}, or {None, False}, The None is not important
        if False in asset_data:
            return False
        # Now only None remains
        return None

    def get_asset_data(self) -> List['ItemArchivalStatus']:
        media_objects: Iterable['Media'] = (
            Media.objects.all().filter(entry_id=self.entry.id).filter(archive_status=STATUS_ARCHIVED)
        )
        return [
            ItemArchivalStatus(
                id=media_object.id,
                last_modify_date=media_object.modified,
                archive_id=media_object.archive_id,
                last_archival_date=media_object.archive_date,
                changed_since_archival=media_object.modified > media_object.archive_date
            )
            for media_object in media_objects
        ]

    def has_entry_changed(self) -> Optional[bool]:
        if self.entry.archive_date is None:
            return None
        return self.entry.date_changed > self.entry.archive_date

    def get_redis_data(self) -> List['ItemArchivalStatus']:
        media_dictionaries: Iterable[dict] = Media.objects\
            .values('id', 'modified')\
            .filter(entry_id=self.entry.id).filter(
                    archive_status__in=[
                        STATUS_ARCHIVE_IN_UPDATE, STATUS_TO_BE_ARCHIVED, STATUS_ARCHIVE_IN_PROGRESS,
                    ]
                )

        if not media_dictionaries:
            return []

        media_jobs = Job.fetch_many(
            [Media.create_archive_job_id(media_dictionary['id']) for media_dictionary in media_dictionaries],
            connection=django_rq.get_connection()
        )

        # Job.fetch_many returns None for not found jobs
        media_jobs = [media_job for media_job in media_jobs if media_job]

        result = []

        for media_job in media_jobs:
            archiver: 'MediaArchiver' = media_job.args[0]
            for media_dictionary in media_dictionaries:
                if archiver.media_object.id == media_dictionary['id']:
                    break
            else:
                raise RuntimeError('Redis media object is missing in database')

            result.append(ItemArchivalStatus(
                id=media_dictionary['id'],
                last_modify_date=media_dictionary['modified'],
                archive_id=None,
                last_archival_date=archiver.archive_data.archive_date,
                changed_since_archival=media_dictionary['modified'] > archiver.archive_data.archive_date
            ))
        return result
