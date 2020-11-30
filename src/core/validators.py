import json

from jsonschema import Draft4Validator, FormatChecker, ValidationError as SchemaValidationError, validate

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .schemas import get_keywords_jsonschema, get_texts_jsonschema, get_type_jsonschema


def validate_type(value):
    try:
        validate(value, get_type_jsonschema(), cls=Draft4Validator, format_checker=FormatChecker())
    except SchemaValidationError as e:
        msg = _('Invalid type: %(error)s') % {'error': e.message}  # noqa: B306
        raise ValidationError(msg)


def validate_keywords(value):
    try:
        validate(value, get_keywords_jsonschema(), cls=Draft4Validator, format_checker=FormatChecker())
        if len(value) > len({json.dumps(d, sort_keys=True) for d in value}):
            raise ValidationError(_('Keywords contains duplicate entries'))
    except SchemaValidationError as e:
        msg = _('Invalid keywords: %(error)s') % {'error': e.message}  # noqa: B306
        raise ValidationError(msg)


def validate_texts(value):
    try:
        validate(value, get_texts_jsonschema(), cls=Draft4Validator, format_checker=FormatChecker())
        for i in value:
            data = i.get('data')
            if data:
                languages = []
                for d in data:
                    languages.append(json.dumps(d['language'], sort_keys=True))
                if len(languages) > len(set(languages)):
                    raise ValidationError(_('Same language is defined multiple times'))
    except SchemaValidationError as e:
        msg = _('Invalid texts: %(error)s') % {'error': e.message}  # noqa: B306
        raise ValidationError(msg)
