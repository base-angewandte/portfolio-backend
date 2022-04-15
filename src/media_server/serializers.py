from rest_framework import serializers

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import Entry

from .validators import validate_license as vl


def validate_license(value):
    if value is not None:
        try:
            vl(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.message) from e  # noqa: B306
    return value


class MediaCreateSerializer(serializers.Serializer):
    file = serializers.FileField()
    entry = serializers.CharField()
    published = serializers.BooleanField()
    license = serializers.JSONField()

    def validate_entry(self, value):
        try:
            entry = Entry.objects.get(id=value)
        except Entry.DoesNotExist as e:
            raise serializers.ValidationError(_('Entry does not exist')) from e
        user = self.context['request'].user
        if user != entry.owner:
            raise serializers.ValidationError(_('Current user is not the owner of entry'))
        return value

    def validate_license(self, value):
        return validate_license(value)


class MediaUpdateSerializer(serializers.Serializer):
    published = serializers.BooleanField()


class MediaPartialUpdateSerializer(serializers.Serializer):
    published = serializers.BooleanField(required=False)
    license = serializers.JSONField(required=False)
    featured = serializers.BooleanField(required=False)

    def validate_license(self, value):
        return validate_license(value)
