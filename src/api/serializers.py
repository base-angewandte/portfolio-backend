from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import Entity, Relation


class CleanModelSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs


class EntitySerializer(CleanModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Entity
        fields = '__all__'


class RelationSerializer(CleanModelSerializer):
    class Meta:
        model = Relation
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=Relation.objects.all(),
                fields=Relation._meta.unique_together[0],
                message=_('Relation already exists'),
            )
        ]

    def __validate_owner(self, value):
        user = self.context['request'].user
        if user != value.owner:
            raise serializers.ValidationError(_('Current user is not the owner of this entity'))
        return value

    def validate_from_entity(self, value):
        return self.__validate_owner(value)

    def validate_to_entity(self, value):
        return self.__validate_owner(value)
