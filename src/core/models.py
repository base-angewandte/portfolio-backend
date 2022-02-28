import django_rq
from jsonschema import Draft4Validator, FormatChecker, ValidationError as SchemaValidationError, validate

from django.apps import apps
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import get_language, gettext_lazy as _

from general.models import AbstractBaseModel, ShortUUIDField
from showroom_connector import sync

from .managers import EntryManager
from .schemas import ICON_DEFAULT, get_icon, get_jsonschema, get_schema
from .skosmos import get_altlabel_lazy, get_preflabel_lazy
from .validators import validate_keywords, validate_texts, validate_type


class Entry(AbstractBaseModel):
    id = ShortUUIDField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(verbose_name=get_preflabel_lazy('title'), max_length=255)
    subtitle = models.CharField(verbose_name=get_preflabel_lazy('subtitle'), max_length=255, blank=True, null=True)
    type = JSONField(verbose_name=get_preflabel_lazy('type'), validators=[validate_type], blank=True, null=True)
    notes = models.TextField(verbose_name=get_preflabel_lazy('notes'), blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    keywords = JSONField(
        verbose_name=get_preflabel_lazy('keywords'),
        validators=[validate_keywords],
        blank=True,
        null=True,
    )
    texts = JSONField(verbose_name=get_preflabel_lazy('text'), validators=[validate_texts], blank=True, null=True)
    published = models.BooleanField(default=False)
    data = JSONField(blank=True, null=True)
    relations = models.ManyToManyField('self', through='Relation', symmetrical=False, related_name='related_to')

    objects = EntryManager()

    class Meta:
        indexes = [
            GinIndex(fields=['type']),
            GinIndex(fields=['data']),
        ]

    @property
    def icon(self):
        if self.type:
            return get_icon(self.type.get('source'))
        return ICON_DEFAULT

    @property
    def location_display(self):
        if self.type.get('source'):
            schema = get_schema(self.type['source'])
            data = self.data
            if schema and data:
                return schema().location_display(data)

    @property
    def owner_role_display(self):
        if self.type.get('source'):
            schema = get_schema(self.type['source'])
            data = self.data
            if schema and data:
                return schema().role_display(data, self.owner.username)

    @property
    def year_display(self):
        if self.type.get('source'):
            schema = get_schema(self.type['source'])
            data = self.data
            if schema and data:
                return schema().year_display(data)

    @property
    def data_display(self):
        ret = {
            'id': self.id,
            'data': [],
        }
        lang = get_language() or 'en'
        for field in ['title', 'subtitle', 'type', 'keywords']:
            value = getattr(self, field)
            if value:
                if isinstance(value, dict):
                    value = value.get('label', {}).get(lang)
                elif isinstance(value, list):
                    value = [x.get('label', {}).get(lang) for x in value]
                ret['data'].append({'label': self._meta.get_field(field).verbose_name, 'value': value})
        if self.texts:
            texts = []
            language_source = f'http://base.uni-ak.ac.at/portfolio/languages/{lang}'
            for text in self.texts:
                text_type = text.get('type', {}).get('label', {}).get(lang) or None
                if text.get('data'):
                    if len(text['data']) > 1:
                        for t in text['data']:
                            if t.get('language', {}).get('source') == language_source:
                                texts.append({'label': text_type, 'value': t.get('text')})
                    else:
                        t = text['data'][0]
                        texts.append({'label': text_type, 'value': t.get('text')})
            if texts:
                ret['data'].append({'label': get_altlabel_lazy('text'), 'value': texts})
        if self.type:
            schema = get_schema(self.type.get('source'))
            data = self.data
            if schema and data:
                ret['data'] += schema().data_display(data)
        return ret

    def clean(self):
        if self.type:
            if self.data:
                schema = get_jsonschema(self.type.get('source'), force_text=True)
                if schema is None:
                    msg = _('Type %(type_source)s does not belong to any active schema') % {
                        'type_source': self.type.get('source')
                    }
                    raise ValidationError(msg)
                try:
                    validate(self.data, schema, cls=Draft4Validator, format_checker=FormatChecker())
                except SchemaValidationError as e:
                    msg = _('Invalid data: %(error)s') % {'error': e.message}  # noqa: B306
                    raise ValidationError(msg)
        elif self.data:
            raise ValidationError(_('Data without type'))

    def add_relation(self, entry):
        relation, created = Relation.objects.get_or_create(
            from_entry=self,
            to_entry=entry,
        )
        return relation

    def remove_relation(self, entry):
        Relation.objects.filter(
            from_entry=self,
            to_entry=entry,
        ).delete()
        return True

    def get_relations(self):
        return self.relations.all()

    def get_related_to(self):
        return self.related_to.all()


class Relation(AbstractBaseModel):
    id = ShortUUIDField(primary_key=True)
    from_entry = models.ForeignKey(Entry, related_name='from_entries', on_delete=models.CASCADE)
    to_entry = models.ForeignKey(Entry, related_name='to_entries', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            'from_entry',
            'to_entry',
        )

    def clean(self):
        if self.from_entry.owner != self.to_entry.owner:
            raise ValidationError(_('Both entries must belong to the same user'))


@receiver(pre_save, sender=Relation)
def relation_pre_save(sender, instance, *args, **kwargs):
    # ensure that there's only one relation between two entries
    instance.to_entry.remove_relation(instance.from_entry)


@receiver(post_save, sender=Entry)
def entry_post_save(sender, instance, created, *args, **kwargs):
    queue = django_rq.get_queue('default')
    if instance.published:
        queue.enqueue(sync.push_entry, entry=instance)
        # TODO: discuss and implement failure handling
        # now check for all attached media that are also published and push those too
        # TODO: discuss: it would be more efficient to only do this if the published
        #       status itself has changed (vs. all the time anything in an already
        #       published entry was changed), but we would need to write our own
        #       update function in the serializer, to set the update_fields in kwargs
        media_model = apps.get_model('media_server', 'Media')
        published_media = media_model.objects.filter(entry_id=instance.id, published=True)
        for medium in published_media:
            queue.enqueue(sync.push_medium, medium=medium)
        # TODO: similar to media also relations would only have to be pushed after
        #       publishing and not on every save
        if instance.from_entries.count():
            queue.enqueue(sync.push_relations, entry=instance)
    # if the instance was just created but not published, we do nothing. but if its
    # published status (now) is false and it was not just created, we have to delete
    # it from Showroom
    elif not created:
        queue.enqueue(sync.delete_entry, entry=instance)
        # TODO: discuss and implement failure handling


@receiver(post_delete, sender=Entry)
def entry_post_delete(sender, instance, *args, **kwargs):
    if instance.published:
        queue = django_rq.get_queue('default')
        queue.enqueue(sync.delete_entry, entry=instance)
        # TODO: discuss and implement failure handling


@receiver(post_save, sender=Relation)
def relation_post_save(sender, instance, *args, **kwargs):
    if instance.from_entry.published and instance.to_entry.published:
        queue = django_rq.get_queue('default')
        queue.enqueue(sync.push_relations, entry=instance.from_entry)
        # TODO: discuss and implement failure handling


@receiver(post_delete, sender=Relation)
def relation_post_delete(sender, instance, *args, **kwargs):
    if instance.from_entry.published and instance.to_entry.published:
        queue = django_rq.get_queue('default')
        queue.enqueue(sync.push_relations, entry=instance.from_entry)
        # TODO: discuss and implement failure handling
