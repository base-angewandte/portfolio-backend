from rest_framework import serializers

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from core.models import Entry

from .validators import validate_license as vl


def validate_license(value):
    if value:
        try:
            vl(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.message)  # noqa: B306
    return value


class MediaCreateSerializer(serializers.Serializer):
    file = serializers.FileField()
    entry = serializers.CharField()
    published = serializers.BooleanField()
    license = serializers.JSONField(required=False)

    def validate_entry(self, value):
        try:
            entry = Entry.objects.get(id=value)
        except Entry.DoesNotExist:
            raise serializers.ValidationError(_('Entry does not exist'))
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

    def validate_license(self, value):
        return validate_license(value)


class ArchiveSerializer(serializers.Serializer):
    published = serializers.BooleanField(required=False)
    license = serializers.JSONField(required=False)

    def validate_license(self, value):
        return validate_license(value)
