from collections import OrderedDict

from rest_framework import serializers

from core.models import Entity
from . import CleanModelSerializer
from .fields import SwaggerSerializerField


class EntityModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = '__all__'


ems = EntityModelSerializer()


class EntitySerializer(CleanModelSerializer):
    id = SwaggerSerializerField(
        ems.fields.get('id').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **ems.fields.get('id')._kwargs,
    )
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    date_created = SwaggerSerializerField(
        ems.fields.get('date_created').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **ems.fields.get('date_created')._kwargs,
    )
    date_changed = SwaggerSerializerField(
        ems.fields.get('date_changed').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **ems.fields.get('date_changed')._kwargs,
    )
    reference = SwaggerSerializerField(
        ems.fields.get('reference').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **ems.fields.get('reference')._kwargs,
    )

    class Meta:
        model = Entity
        fields = '__all__'
