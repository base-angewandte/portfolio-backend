from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from jsonschema import validate, ValidationError as SchemaValidationError

from general.models import AbstractBaseModel, ShortUUIDField
from .schemas import ACTIVE_TYPES_CHOICES, get_jsonschema
from .skosmos import get_preflabel_lazy


class Entity(AbstractBaseModel):
    @staticmethod
    def get_type_choices(lang=None):
        return ACTIVE_TYPES_CHOICES

    TYPE_CHOICES = lazy(get_type_choices.__func__, tuple)()

    id = ShortUUIDField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(verbose_name=get_preflabel_lazy('c_title'), max_length=255)
    subtitle = models.CharField(verbose_name=get_preflabel_lazy('c_subtitle'), max_length=255, blank=True, null=True)
    type = models.CharField(
        verbose_name=get_preflabel_lazy('c_type'), max_length=255, choices=TYPE_CHOICES, blank=True, null=True,
    )
    notes = models.TextField(verbose_name=get_preflabel_lazy('c_notes'), blank=True, null=True)
    reference = models.CharField(verbose_name=get_preflabel_lazy('c_reference'), max_length=255, blank=True, null=True)
    keywords = ArrayField(
        models.CharField(max_length=255, verbose_name=get_preflabel_lazy('c_keywords')),
        default=list,
        blank=True,
    )
    data = JSONField(blank=True, null=True)
    relations = models.ManyToManyField('self', through='Relation', symmetrical=False, related_name='related_to')

    def clean(self):
        if self.type:
            if self.data:
                schema = get_jsonschema(self.type, force_text=True)
                try:
                    validate(self.data, schema)
                except SchemaValidationError as e:
                    raise ValidationError(_('Invalid data: {}'.format(e.message)))
        elif self.data:
            raise ValidationError(_('Data without type'))

    def add_relation(self, entity):
        relation, created = Relation.objects.get_or_create(
            from_entity=self,
            to_entity=entity,
        )
        return relation

    def remove_relation(self, entity):
        Relation.objects.filter(
            from_entity=self,
            to_entity=entity,
        ).delete()
        return True

    def get_relations(self):
        return self.relations.all()

    def get_related_to(self):
        return self.related_to.all()


class Relation(AbstractBaseModel):
    id = ShortUUIDField(primary_key=True)
    from_entity = models.ForeignKey(Entity, related_name='from_entities', on_delete=models.CASCADE)
    to_entity = models.ForeignKey(Entity, related_name='to_entities', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('from_entity', 'to_entity',)

    def clean(self):
        if self.from_entity.owner != self.to_entity.owner:
            raise ValidationError(_('Both entities must belong to the same user'))


@receiver(pre_save, sender=Relation)
def relation_pre_save(sender, instance, *args, **kwargs):
    # ensure that there's only one relation between two entities
    instance.to_entity.remove_relation(instance.from_entity)
