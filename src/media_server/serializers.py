from rest_framework import serializers

from core.models import Entity


class MediaSerializer(serializers.Serializer):
    file = serializers.FileField()
    parent = serializers.CharField()

    def validate_parent(self, value):
        try:
            parent = Entity.objects.get(id=value)
        except Entity.DoesNotExist:
            raise serializers.ValidationError(_('Parent does not exist'))
        user = self.context['request'].user
        if user != parent.owner:
            raise serializers.ValidationError(_('Current user is not the owner of parent'))
        return value
