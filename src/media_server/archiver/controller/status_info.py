from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional

from media_server.archiver import STATUS_ARCHIVED
from media_server.archiver.utilities import DateTimeComparator
from media_server.models import Media

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
    threshold_entry: Optional[int]
    threshold_asset: Optional[int]

    def __init__(self, entry: 'Entry', threshold_entry: Optional[int] = None, threshold_asset: Optional[int] = None):
        """

        :param entry:
        :param threshold_entry: Time in seconds, since when to consider an entry changed after archival
        :param threshold_asset: Time in seconds, since when to consider an asset/media changed after archival
        """
        self.threshold_asset = threshold_asset
        self.threshold_entry = threshold_entry
        self.entry_date_time_comparator = DateTimeComparator(max_seconds=self.threshold_entry)
        self.assets_date_time_comparator = DateTimeComparator(max_seconds=self.threshold_asset)
        self.entry = entry

    @property
    def data(self) -> 'EntryArchivalStatus':
        asset_data = self.get_asset_data()
        return EntryArchivalStatus(
            entry=ItemArchivalStatus(
                id=self.entry.id,
                last_modify_date=self.entry.date_changed,
                archive_id=self.entry.archive_id,
                last_archival_date=self.entry.archive_date,
                changed_since_archival=self.has_entry_changed(),
            ),
            assets=asset_data,
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

        # Any changed value makes the whole thing changed
        if True in asset_data:
            return True
        # if {False}, or {None, False}, The None is not important
        if False in asset_data:
            return False
        # Now only None remains
        return None

    def get_asset_data(self) -> List['ItemArchivalStatus']:
        media_objects: Iterable['Media'] = (
            Media.objects.all().filter(entry_id=self.entry.id).filter(archive_status=STATUS_ARCHIVED)
        )
        date_time_comparator = DateTimeComparator(max_seconds=self.threshold_asset)
        return [
            ItemArchivalStatus(
                id=media_object.id,
                last_modify_date=media_object.modified,
                archive_id=media_object.archive_id,
                last_archival_date=media_object.archive_date,
                changed_since_archival=date_time_comparator.greater_then(
                    media_object.modified, media_object.archive_date
                ),
            )
            for media_object in media_objects
        ]

    def has_entry_changed(self) -> bool:
        return self.entry_date_time_comparator.greater_then(self.entry.date_changed, self.entry.archive_date)
