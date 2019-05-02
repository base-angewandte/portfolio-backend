from rest_framework import serializers

from core.models import Entry


class MediaCreateSerializer(serializers.Serializer):
    file = serializers.FileField()
    entry = serializers.CharField()
    published = serializers.BooleanField()
    license = serializers.CharField(required=False)

    def validate_entry(self, value):
        try:
            entry = Entry.objects.get(id=value)
        except Entry.DoesNotExist:
            raise serializers.ValidationError(_('Entry does not exist'))
        user = self.context['request'].user
        if user != entry.owner:
            raise serializers.ValidationError(_('Current user is not the owner of entry'))
        return value


class MediaUpdateSerializer(serializers.Serializer):
    published = serializers.BooleanField()


class MediaPartialUpdateSerializer(serializers.Serializer):
    published = serializers.BooleanField(required=False)
    license = serializers.CharField(required=False)
