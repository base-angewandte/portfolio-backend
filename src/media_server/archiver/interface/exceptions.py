from abc import abstractmethod

from rest_framework import status
from rest_framework.exceptions import APIException

from media_server.archiver.messages import errors


class InternalValidationError(RuntimeError):
    """When then internal data structure is no well defined, but the user does
    not need to be concerned."""

    pass


class ExternalServerError(APIException):
    """External has an error."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    @property
    @abstractmethod
    def external_service_name(self) -> str:
        """
        :return: The name of the external service
        """
        pass

    @property
    def default_detail(self) -> str:
        return errors.external_service_unavailable(self.external_service_name)

    @property
    def default_code(self) -> str:
        return 'service_unavailable'