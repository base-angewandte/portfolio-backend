from django.utils.translation import gettext as _

from . import thesis

# Translators: Default message for fields with no value
FIELD_MAY_NOT_BE_NULL = _('Field may not be null.')

# Translators: Default message for empty required fields
MISSING_DATA_FOR_REQUIRED_FIELD = _('Missing data for required field.')

# Translators: Default message for invalid type, for example a number is requested and en e-mail-address is given
INVALID_TYPE = _('Invalid type.')

# Translators: Default message, when validation failed to unknown reason
INVALID = _('Invalid value.')

# so flake does not throw an unused import error on from . import thesis
__all__ = ['thesis', 'FIELD_MAY_NOT_BE_NULL', 'MISSING_DATA_FOR_REQUIRED_FIELD', 'INVALID_TYPE', 'INVALID']
