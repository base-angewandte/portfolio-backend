from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from jsonschema import validate, ValidationError as SchemaValidationError

from .schemas import get_license_jsonschema


def validate_license(value):
    try:
        validate(value, get_license_jsonschema())
    except SchemaValidationError as e:
        msg = _('Invalid license: %(error)s') % {'error': e.message}
        raise ValidationError(msg)
