from collections import OrderedDict

from django.conf import settings
from django.urls import reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from core.models import Entry, Relation
from core.skosmos import get_preflabel_lazy
from core.utils import placeholder_lazy
from media_server.models import get_image_for_entry, has_entry_media
from . import CleanModelSerializer, SwaggerMetaModelSerializer


class RelatedEntrySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ('id', 'title', 'type', 'image', )
        read_only_fields = fields

    def get_image(self, obj) -> str:
        return get_image_for_entry(obj.pk)


class RelationsSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    to = RelatedEntrySerializer(read_only=True)


class EntrySerializer(CleanModelSerializer, SwaggerMetaModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    relations = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    has_media = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = '__all__'
        swagger_meta_attrs = {
            'id': OrderedDict([('hidden', True)]),
            'date_created': OrderedDict([('hidden', True)]),
            'date_changed': OrderedDict([('hidden', True)]),
            'reference': OrderedDict([('hidden', True)]),
            'published': OrderedDict([('hidden', True)]),
            'data': OrderedDict([('hidden', True)]),
            # switched field type from autocomplete to text until autocomplete actually supported
            # TODO: switch back to autocomplete
            'title': OrderedDict([('field_type', 'text'), ('field_format', 'half'), ('order', 1)]),
            'subtitle': OrderedDict([('field_type', 'text'), ('field_format', 'half'), ('order', 2)]),
            'type': OrderedDict([
                ('field_type', 'chips'),
                ('source', reverse_lazy('jsonschema-list', kwargs={'version': 'v1'})),
                ('order', 3),
            ]),
            'texts': OrderedDict([('field_type', 'multiline'),
                                  ('source_type', 'https://voc.uni-ak.ac.at/skosmos/rest/v1/portfolio/search?lang=de&parent=http://base.uni-ak.ac.at/portfolio/cv/text_type'),
                                  ('order', 4)]),
            'keywords': OrderedDict([
                ('field_type', 'chips'),
                ('source', reverse_lazy('lookup_all', kwargs={'version': 'v1', 'fieldname': 'keywords'}),),
                ('order', 5),
                ('allow_unkown_entries', True),
                ('dynamic_autosuggest', True,),
                ('set_label_language', True,),
            ]),
            'notes': OrderedDict([
                ('field_type', 'multiline'),
                ('order', 6),
                (
                    'placeholder',
                    format_lazy('{} ({})', placeholder_lazy(get_preflabel_lazy('notes')), _('will not be published'))
                ),
            ]),
            'icon': OrderedDict([('hidden', True)]),
            'has_media': OrderedDict([('hidden', True)]),
        }

    @swagger_serializer_method(serializer_or_field=RelationsSerializer)
    def get_relations(self, obj):
        ret = []
        for relation in Relation.objects.select_related('to_entry').filter(from_entry=obj):
            ret.append({
                'id': relation.pk,
                'to': {
                    'id': relation.to_entry.pk,
                    'title': relation.to_entry.title,
                    'type': relation.to_entry.type,
                    'image': get_image_for_entry(relation.to_entry.pk),
                }
            })
        return ret

    def get_icon(self, obj) -> str:
        return obj.icon

    def get_has_media(self, obj) -> bool:
        return has_entry_media(obj.pk)
