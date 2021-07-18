import typing

from rest_framework.exceptions import ValidationError

from ...interface.abstractarchiver import AbstractArchiver
from ...interface.responses import SuccessfulArchiveResponse
from .media.archiver import MediaArchiveHandler
from .metadata.archiver import DefaultMetadataArchiver, ThesisMetadataArchiver


class PhaidraArchiver(AbstractArchiver):
    """Archives to Phaidra https://app.swaggerhub.com/apis/ctot-
    nondef/Phaidra/1.0.0#/"""

    _metadata_data_archiver: typing.Optional[AbstractArchiver] = None

    @property
    def metadata_data_archiver(self) -> AbstractArchiver:
        if self._metadata_data_archiver is None:
            if self.archive_object.entry.is_thesis:
                self._metadata_data_archiver = ThesisMetadataArchiver(self.archive_object)
            else:
                self._metadata_data_archiver = DefaultMetadataArchiver(self.archive_object)
        return self._metadata_data_archiver

    _media_archiver: typing.Optional[AbstractArchiver] = None

    @property
    def media_archiver(self) -> AbstractArchiver:
        if self._media_archiver is None:
            self._media_archiver = MediaArchiveHandler(self.archive_object)
        return self._media_archiver

    def validate(self) -> None:
        validation_errors = []
        for archiver in (self.metadata_data_archiver, self.media_archiver):
            try:
                archiver.validate()
            except ValidationError as validation_error:
                validation_errors.append(validation_error)
        if validation_errors:
            raise ValidationError(
                {
                    field: messages
                    for validation_error in validation_errors
                    for field, messages in validation_error.detail.items()
                }
            )

    def push_to_archive(self) -> SuccessfulArchiveResponse:
        metadata_response = self.metadata_data_archiver.push_to_archive()
        self.media_archiver.push_to_archive()
        return metadata_response

    def update_archive(self) -> 'SuccessfulArchiveResponse':
        return self.metadata_data_archiver.update_archive()
