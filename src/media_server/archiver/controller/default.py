from typing import TYPE_CHECKING, Optional, Set

from rest_framework.exceptions import APIException, PermissionDenied

from django.contrib.auth.models import User

from core.models import Entry
from media_server.archiver import messages

from ...models import Media
from ..factory.default import ArchiverFactory
from ..interface.archiveobject import ArchiveObject

if TYPE_CHECKING:
    from ..interface.abstractarchiver import AbstractArchiver
    from ..interface.responses import SuccessfulArchiveResponse


class DefaultArchiveController:
    """Handle Archive Actions."""

    user: User
    media_objects: Set['Media']
    _entry: Optional[Entry]

    @property
    def entry(self) -> Entry:
        if self._entry is None:
            self._entry = self._get_entry()
        return self._entry

    _archiver: Optional['AbstractArchiver'] = None

    @property
    def archiver(self) -> 'AbstractArchiver':
        if self._archiver is None:
            self._archiver = self._create_archiver()
        return self._archiver

    def __init__(self, user: User, media_objects: Set['Media'], entry: Optional[Entry] = None):
        """
        :param user: The user, the request is coming from
        :param media_objects: the media to archive
        """
        self.media_objects = media_objects
        self.user = user
        self._entry = entry

    def push_to_archive(self) -> 'SuccessfulArchiveResponse':
        """Validates the data and pushes to archive.

        :raises media_server.archiver.interface.exceptions.ExternalServerError
        :return: SuccessfulArchiveResponse
        """
        self.validate()
        return self._push_to_archive()

    def validate(self):
        """Check if the request will comply to internal and external rules.

        :raises ValidationError, PermissionDenied
        :return:
        """
        self._validate_ownership()
        self._validate_for_archive()

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        self.validate()
        return self._update_archive()

    def _validate_for_archive(self) -> None:
        """Check if external rules are complied.

        :raises ValidationError
        :return:
        """
        self._create_archiver()
        self.archiver.validate()

    def _push_to_archive(self) -> 'SuccessfulArchiveResponse':
        """Push to archive.

        :raises media_server.archiver.interface.exceptions.ExternalServerError
        :return:
        """
        self._create_archiver()
        return self.archiver.push_to_archive()

    def _get_entry(self) -> Entry:
        """
        Get the common entry for all media objects
        :return:
        """
        entry_primary_keys = {media.entry_id for media in self.media_objects}
        n_entries = len(entry_primary_keys)
        if n_entries != 1:
            raise APIException(messages.errors.assets_belong_to_not_one_entry(n_entries))
        return Entry.objects.get(pk=entry_primary_keys.pop())

    def _validate_ownership(self):
        """Check if entry owner and user (from request) are the same.

        :raises PermissionDenied
        :return:
        """
        if not (self.entry.owner == self.user):
            raise PermissionDenied(messages.errors.CURRENT_USER_NOW_OWNER_OF_MEDIA)

    def _create_archiver(self) -> 'AbstractArchiver':
        """
        Create an archiver instance
        :return:
        """
        return ArchiverFactory().create(
            ArchiveObject(user=self.user, entry=self.entry, media_objects=self.media_objects)
        )

    def _update_archive(self):
        self._create_archiver()
        return self.archiver.update_archive()
