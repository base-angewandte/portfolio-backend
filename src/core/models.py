from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from jsonschema import validate, ValidationError as SchemaValidationError

from general.models import AbstractBaseModel, ShortUUIDField
from .managers import EntryManager
from .schemas import ICON_DEFAULT, get_jsonschema, get_icon
from .skosmos import get_preflabel_lazy
from .validators import validate_texts, validate_keywords, validate_type


class Entry(AbstractBaseModel):
    id = ShortUUIDField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(verbose_name=get_preflabel_lazy('title'), max_length=255)
    subtitle = models.CharField(
        verbose_name=get_preflabel_lazy('subtitle'), max_length=255, blank=True, null=True,
    )
    type = JSONField(verbose_name=get_preflabel_lazy('type'), validators=[validate_type], blank=True, null=True)
    notes = models.TextField(verbose_name=get_preflabel_lazy('notes'), blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    keywords = JSONField(
        verbose_name=get_preflabel_lazy('keywords'), validators=[validate_keywords], blank=True, null=True,
    )
    texts = JSONField(verbose_name=get_preflabel_lazy('text'), validators=[validate_texts], blank=True, null=True)
    published = models.BooleanField(default=False)
    data = JSONField(blank=True, null=True)
    relations = models.ManyToManyField('self', through='Relation', symmetrical=False, related_name='related_to')

    objects = EntryManager()

    @property
    def icon(self):
        if self.type:
            return get_icon(self.type)
        return ICON_DEFAULT

    def clean(self):
        if self.type:
            if self.data:
                schema = get_jsonschema(self.type, force_text=True)
                try:
                    validate(self.data, schema)
                except SchemaValidationError as e:
                    msg = _('Invalid data: %(error)s') % {'error': e.message}
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
        unique_together = ('from_entry', 'to_entry',)

    def clean(self):
        if self.from_entry.owner != self.to_entry.owner:
            raise ValidationError(_('Both entries must belong to the same user'))


@receiver(pre_save, sender=Relation)
def relation_pre_save(sender, instance, *args, **kwargs):
    # ensure that there's only one relation between two entries
    instance.to_entry.remove_relation(instance.from_entry)
