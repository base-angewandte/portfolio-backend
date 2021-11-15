from dataclasses import dataclass
from datetime import datetime
from typing import Set, Union

from django.contrib.auth.models import User

from core.models import Entry
from media_server.models import Media


@dataclass
class ArchiveObject:
    """This is a wrapper for what implementations of
    `.abstractarchiver.AbstractArchiver` can expect to handle."""

    user: User
    """
    The user who owns the entry, the media and sends the request
    """
    entry: Entry
    """
    The entry, that belongs to the media
    """
    media_objects: Set[Media]
    """
    The media to be archived
    """


@dataclass
class ArchiveData:
    """
    Contains generated data for archival (at a latter point)
    """
    archive_date: datetime
    """
    The timestamp, when the user requested archival – to be used later in saving
    """
    data: Union[dict, list]
    """
    The data for archival, validated and in the format, the provider expects
    """
