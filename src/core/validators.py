from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from jsonschema import validate, ValidationError as SchemaValidationError

from .schemas import get_text_jsonschema


def validate_text(value):
    try:
        validate(value, get_text_jsonschema())
        for i in value:
            data = i.get('data')
            if data:
                languages = []
                for d in data:
                    languages.append(d['language'])
                if len(languages) > len(set(languages)):
                    raise ValidationError(_('Same language is defined multiple times'))
    except SchemaValidationError as e:
        raise ValidationError(_('Invalid text: {}'.format(e.message)))
