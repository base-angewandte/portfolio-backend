from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from jsonschema import validate, ValidationError as SchemaValidationError

from .schemas import get_texts_jsonschema, get_keywords_jsonschema


def validate_keywords(value):
    try:
        validate(value, get_keywords_jsonschema())
        if len(value) > len(set(map(tuple, map(dict.items, value)))):
            raise ValidationError(_('Keywords contains duplicate entries'))
    except SchemaValidationError as e:
        raise ValidationError(_('Invalid keywords: {}'.format(e.message)))


def validate_texts(value):
    try:
        validate(value, get_texts_jsonschema())
        for i in value:
            data = i.get('data')
            if data:
                languages = []
                for d in data:
                    languages.append(d['language'])
                if len(languages) > len(set(languages)):
                    raise ValidationError(_('Same language is defined multiple times'))
    except SchemaValidationError as e:
        raise ValidationError(_('Invalid texts: {}'.format(e.message)))
