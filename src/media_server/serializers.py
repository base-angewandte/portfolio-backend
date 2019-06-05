from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from core.models import Entry
from .validators import validate_license


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
        if value:
            try:
                validate_license(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.message)
        return value


class MediaUpdateSerializer(serializers.Serializer):
    published = serializers.BooleanField()


class MediaPartialUpdateSerializer(serializers.Serializer):
    published = serializers.BooleanField(required=False)
    license = serializers.JSONField(required=False)

    def validate_license(self, value):
        if value:
            try:
                validate_license(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.message)
        return value
