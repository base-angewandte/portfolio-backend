from enum import Enum

from rest_framework.response import Response

from django.utils.translation import gettext


class ModificationType(Enum):
    created = 'created'
    updated = 'updated'
    uploaded: 'uploaded'


class SuccessfulArchiveResponse(Response):
    def __init__(self, modification_type: ModificationType, object_description: str, service: str):
        super().__init__(
            {
                'action': modification_type.value,
                'object': object_description,
                'servive': service,
                'message': gettext('Successfully %(action) %(object) to %(service)')
                % {
                    'action': modification_type.value,
                    'object': object_description,
                    'servive': service,
                },
            }
        )
