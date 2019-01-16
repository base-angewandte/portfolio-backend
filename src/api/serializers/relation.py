from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import Relation
from . import CleanModelSerializer
from .fields import SwaggerSerializerField


class RelationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = '__all__'


rms = RelationModelSerializer()


class RelationSerializer(CleanModelSerializer):
    id = SwaggerSerializerField(
        rms.fields.get('id').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **rms.fields.get('id')._kwargs,
    )
    date_created = SwaggerSerializerField(
        rms.fields.get('date_created').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **rms.fields.get('date_created')._kwargs,
    )
    date_changed = SwaggerSerializerField(
        rms.fields.get('date_changed').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **rms.fields.get('date_changed')._kwargs,
    )

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
