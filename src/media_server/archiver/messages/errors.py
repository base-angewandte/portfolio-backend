from django.utils.translation import gettext as _

# Translators: Something goes wrong and the media for archival is not found.
MEDIA_NOT_FOUND = _('Media assets do not exist')


def assets_belong_to_not_one_entry(n_entries: int) -> str:
    # Translators: Only media assets of one entry can be archived together. 0 or more than one found
    return _('All media objects must belong to one entry. %(n_entries)d found') % {'n_entries': n_entries}


# Translators: Something goes wrong and the user tried to archive an media asset, which he does not "own"
CURRENT_USER_NOW_OWNER_OF_MEDIA = _('Current user is not the owner of this media object')


def external_service_unavailable(service: str) -> str:
    # Translators: The archival service is unavailable due to unknown reasons
    return _('%(service)s temporarily unavailable, try again later.') % {'service': service}
