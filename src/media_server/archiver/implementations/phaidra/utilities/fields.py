from marshmallow.fields import Constant, List, Nested, String

from media_server.archiver.messages import validation as validation_messages

"""https://marshmallow.readthedocs.io/en/2.x-line/api_reference.html#marshmallow.fields.Field.default_error_messages"""
default_error_messages = {
    'null': validation_messages.FIELD_MAY_NOT_BE_NULL,
    'required': validation_messages.MISSING_DATA_FOR_REQUIRED_FIELD,
    'type': validation_messages.INVALID_TYPE,
    'validator_failed': validation_messages.INVALID,
}


class PortfolioConstantField(Constant):
    default_error_messages = default_error_messages


class PortfolioStringField(String):
    default_error_messages = default_error_messages


class PortfolioListField(List):
    default_error_messages = default_error_messages


class PortfolioNestedField(Nested):
    default_error_messages = default_error_messages
