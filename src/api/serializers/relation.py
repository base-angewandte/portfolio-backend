from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import Relation
from . import CleanModelSerializer


class RelationSerializer(CleanModelSerializer):
    class Meta:
        model = Relation
        fields = ('from_entry', 'to_entry', )

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
            raise serializers.ValidationError(_('Current user is not the owner of this entry'))
        return value

    def validate_from_entry(self, value):
        return self.__validate_owner(value)

    def validate_to_entry(self, value):
        return self.__validate_owner(value)
