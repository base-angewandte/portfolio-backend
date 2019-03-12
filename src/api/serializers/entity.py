from collections import OrderedDict

from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from core.models import Entity, Relation
from media_server.models import get_image_for_entity
from . import CleanModelSerializer
from .fields import SwaggerSerializerField


class RelatedEntitySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = ('id', 'title', 'type', 'image', )
        read_only_fields = fields

    def get_image(self, obj) -> str:
        return get_image_for_entity(obj.pk)


class RelationsSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    to = RelatedEntitySerializer(read_only=True)


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
    published = SwaggerSerializerField(
        ems.fields.get('published').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **ems.fields.get('published')._kwargs,
    )
    data = SwaggerSerializerField(
        ems.fields.get('data').__class__,
        attrs=OrderedDict([('hidden', True)]),
        **ems.fields.get('data')._kwargs,
    )
    title = SwaggerSerializerField(
        ems.fields.get('title').__class__,
        attrs=OrderedDict([
            ('field_type', 'autocomplete'),
            ('field_format', 'half'),
            ('order', 1),
            ('source', 'http://localhost:8200/autosuggest/v1/person/')
        ]),
        **ems.fields.get('title')._kwargs,
    )
    subtitle = SwaggerSerializerField(
        ems.fields.get('subtitle').__class__,
        attrs=OrderedDict([('field_type', 'autocomplete'), ('field_format', 'half'), ('order', 2)]),
        **ems.fields.get('subtitle')._kwargs,
    )
    type = SwaggerSerializerField(
        ems.fields.get('type').__class__,
        attrs=OrderedDict([
            ('field_type', 'chips'),
            ('source', 'http://localhost:8200/api/v1/jsonschema/'),
            ('order', 3)
        ]),
        **ems.fields.get('type')._kwargs,
    )
    texts = SwaggerSerializerField(
        ems.fields.get('texts').__class__,
        attrs=OrderedDict([('field_type', 'multiline'), ('source', ''), ('order', 4)]),
        **ems.fields.get('texts')._kwargs,
    )
    keywords = SwaggerSerializerField(
        ems.fields.get('keywords').__class__,
        attrs=OrderedDict([('field_type', 'chips'), ('source', ''), ('order', 5)]),
        **ems.fields.get('keywords')._kwargs,
    )
    notes = SwaggerSerializerField(
        ems.fields.get('notes').__class__,
        attrs=OrderedDict([('field_type', 'multiline'), ('order', 6)]),
        **ems.fields.get('notes')._kwargs,
    )

    relations = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Entity
        fields = '__all__'

    @swagger_serializer_method(serializer_or_field=RelationsSerializer)
    def get_relations(self, obj):
        ret = []
        for relation in Relation.objects.select_related('to_entity').filter(from_entity=obj):
            ret.append({
                'id': relation.pk,
                'to': {
                    'id': relation.to_entity.pk,
                    'title': relation.to_entity.title,
                    'type': relation.to_entity.type,
                    'image': get_image_for_entity(relation.to_entity.pk),
                }
            })
        return ret
