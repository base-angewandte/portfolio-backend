from enum import Enum

from rest_framework.response import Response

from media_server.archiver import messages


class ModificationType(Enum):
    created = 'created'
    updated = 'updated'
    uploaded = 'uploaded'


class SuccessfulArchiveResponse(Response):
    def __init__(self, modification_type: ModificationType, object_description: str, service: str):
        """

        :param modification_type:
        :param object_description:
        :param service:
        """
        super().__init__(
            {
                'action': modification_type.value,
                'object': object_description,
                'service': service,
                'message': messages.success.successful_archival_message(
                    modification_type.value,
                    object_description,
                    service,
                ),
            }
        )


class SuccessfulValidationResponse(Response):
    pass
