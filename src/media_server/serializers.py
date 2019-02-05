from rest_framework import serializers

from core.models import Entity


class MediaSerializer(serializers.Serializer):
    file = serializers.FileField()
    entity = serializers.CharField()

    def validate_entity(self, value):
        try:
            entity = Entity.objects.get(id=value)
        except Entity.DoesNotExist:
            raise serializers.ValidationError(_('Entity does not exist'))
        user = self.context['request'].user
        if user != entity.owner:
            raise serializers.ValidationError(_('Current user is not the owner of entity'))
        return value
