import json

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from jsonschema import ValidationError as SchemaValidationError, validate

from core.skosmos import get_media_licenses

from .schemas import get_license_jsonschema


def validate_license(value):
    try:
        validate(value, get_license_jsonschema())
    except SchemaValidationError as e:
        msg = _('Invalid license: %(error)s') % {'error': e.message}
        raise ValidationError(msg)

    license_set = set(json.dumps(d, sort_keys=True) for d in get_media_licenses())
    if json.dumps(value, sort_keys=True) not in license_set:
        raise ValidationError(_('Invalid license'))
