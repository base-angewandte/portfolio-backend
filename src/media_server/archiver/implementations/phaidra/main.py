import typing

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
        self.metadata_data_archiver.validate()
        self.media_archiver.validate()

    def push_to_archive(self) -> SuccessfulArchiveResponse:
        metadata_response = self.metadata_data_archiver.push_to_archive()
        self.media_archiver.push_to_archive()
        return metadata_response
