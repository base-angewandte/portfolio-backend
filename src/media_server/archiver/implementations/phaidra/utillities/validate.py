import typing
from typing import Hashable

from marshmallow.validate import Length, Validator, ValidationError

from media_server.archiver.messages import validation as validation_messages


class ValidateLength1(Length):
    """In a lot of cases we have {key: ['is actually on value in portfolio',]}
    which is like key: value, so …"""

    message_min = validation_messages.MISSING_DATA_FOR_REQUIRED_FIELD

    def __init__(self):
        super().__init__(min=1)


class ValidateAuthor(ValidateLength1):
    """As far as I understand it, messages have to be defined at class level,
    so I'll write a validate class for Author."""

    message_min = validation_messages.thesis.MISSING_AUTHOR


class ValidateLanguage(ValidateLength1):
    """As far as I understand it, messages have to be defined at class level,
    so I'll write a validate class for Language."""

    message_min = validation_messages.thesis.MISSING_LANGUAGE


class ValidateSupervisor(ValidateLength1):
    """As far as I understand it, messages have to be defined at class level,
    so I'll write a validate class for Supervisor."""

    message_min = validation_messages.thesis.MISSING_SUPERVISOR


class NotFalsyValidator(Validator):
    """
    If key not present in data, or not data[key] raise validation error.
    """
    message: str
    key: Hashable
    error: str

    def __init__(self, key: typing.Hashable, message: str):
        self.key = key
        self.message = message
        self.error = 'No error yet!'

    def __call__(self, value: dict) -> dict:
        return self.validate(value)

    def validate(self, value: dict) -> dict:
        if (self.key not in value) or (not value[self.key]):
            self.error = self.message
            raise ValidationError(self.message, [self.key, ])
        return value
