from typing import TYPE_CHECKING, Optional, Set, Type

from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

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
    media_primary_keys: Set[str]

    _media_objects: Optional[Set[Media]] = None

    @property
    def media_objects(self) -> Set[Media]:
        if self._media_objects is None:
            self._media_objects = self._create_media_objects()
        return self._media_objects

    _entry: Optional[Entry] = None

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

    def __init__(self, user: User, media_primary_keys: Set[str]):
        """
        :param user: The user, the request is coming from
        :param media_primary_keys: primary keys of the media to archive
        """
        self.user = user
        self.media_primary_keys = media_primary_keys
        if self.media_primary_keys.__len__() == 0:
            raise ValidationError({'media_pks': [_('empty')]})

    @classmethod
    def from_entry(cls, entry: 'Entry') -> 'DefaultArchiveController':
        return cls(
            user=entry.owner, media_primary_keys={media.id for media in Media.objects.all().filter(entry_id=entry.id)}
        )

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

    def _create_media_objects(self) -> Set[Media]:
        """Get all media objects as defined in media_primary_keys from the
        database.

        :raises NotFound
        :return:
        """
        media_objects = set()
        for media_primary_key in self.media_primary_keys:
            try:
                media_objects.add(Media.objects.get(id=media_primary_key))
            except ObjectDoesNotExist:
                raise NotFound(messages.errors.MEDIA_NOT_FOUND)
        return media_objects

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


@receiver(pre_save, sender=Entry)
def entry_pre_save(sender: Type['Entry'], instance: 'Entry', update_fields, *args, **kwargs):
    if instance.archive_id and instance.update_archive:
        DefaultArchiveController.from_entry(instance).update_archive()
