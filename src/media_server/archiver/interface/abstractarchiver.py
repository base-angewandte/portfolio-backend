import typing
from abc import ABC, abstractmethod

from rest_framework.exceptions import ValidationError

from .archiveobject import ArchiveObject

if typing.TYPE_CHECKING:
    from .responses import SuccessfulArchiveResponse


class AbstractArchiver(ABC):
    """Archives Entries."""

    def __init__(self, archive_object: ArchiveObject):
        """Archive Entry from the database to …

        :type archive_object: ArchiveObject
        """
        self.archive_object = archive_object

    @abstractmethod
    def validate(self) -> None:
        """Validate if the fields comply to the target data schema.

        :raises
            ValidationError with a dict of {fieldname: [errors,]. Use portfolios fieldnames, not target schema.
            Translate Error messages!
        :return: None
        """
        pass

    @abstractmethod
    def push_to_archive(self) -> 'SuccessfulArchiveResponse':
        """
        Push to archive and return message
        :raises: media_server.archiver.interface.exceptions.ExternalServerError
        :return: SuccessfulArchiveResponse
        """
        pass

    @abstractmethod
    def update_archive(self) -> 'SuccessfulArchiveResponse':
        """
        Push to archive and return message
        :raises: media_server.archiver.interface.exceptions.ExternalServerError
        :return: SuccessfulArchiveResponse
        """
        pass

    def throw_validation_errors(self, errors: typing.Optional[typing.Dict[str, typing.List[str]]]) -> None:
        """
        :
        :param errors:
        :return:
        """
        if errors:
            raise ValidationError(errors)
