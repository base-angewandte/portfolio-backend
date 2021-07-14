import typing
from typing import TYPE_CHECKING, Dict

from portfolio import settings

from ..implementations.phaidra.main import PhaidraArchiver
from .archives import Archives

if TYPE_CHECKING:
    from ..interface.abstractarchiver import AbstractArchiver
    from ..interface.archiveobject import ArchiveObject


class ArchiverFactory:
    """Generate instances of implementations of `AbstractArchiver`s."""

    mappings: Dict[Archives, typing.Type['AbstractArchiver']] = {Archives.PHAIDRA: PhaidraArchiver}

    def create(
        self, archive_object: 'ArchiveObject', archive: typing.Optional[typing.Union[Archives, str]] = None
    ) -> 'AbstractArchiver':
        """Create a archiver instance for an entry.

        :param archive_object:
        :param archive: defaults to env ARCHIVE_TYPE
        :return: An implementation for an archiver
        """
        archive = archive or settings.ARCHIVE_TYPE
        if archive.__class__ is str:
            try:
                archive = Archives(archive)
            except ValueError:
                raise NotImplementedError(f'{archive} is not registered in the factory')
        if archive not in self.mappings:
            raise NotImplementedError(f'{archive} is not registered in the factory')

        return self.mappings[archive](archive_object)
