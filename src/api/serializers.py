from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import Entity, Relation


class EntitySerializer(serializers.ModelSerializer):
    # owner = serializers.HiddenField(
    #     default=serializers.CurrentUserDefault()
    # )

    class Meta:
        model = Entity
        fields = '__all__'

    def validate(self, attrs):
        instance = Entity(**attrs)
        instance.clean()
        return attrs


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=Relation.objects.all(),
                fields=Relation._meta.unique_together[0],
                message='Relation already exists',
            )
        ]
