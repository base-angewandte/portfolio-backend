from django.utils.translation import gettext as _


def successful_archival_message(modification_type: str, object_description: str, service: str) -> str:
    return _('Successfully %(modification_type)s %(object_description)s to %(service)s') % {
        'modification_type': modification_type,
        'object_description': object_description,
        'service': service,
    }
