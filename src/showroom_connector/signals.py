import django_rq

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.models import Entry, Relation
from media_server.models import STATUS_CONVERTED, Media

from . import sync


@receiver(post_save, sender=Entry)
def entry_post_save(sender, instance, created, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        queue = django_rq.get_queue('default')
        if instance.published:
            entry_sync = queue.enqueue(sync.push_entry, entry=instance)
            # TODO: discuss and implement failure handling
            # now check for all attached media that are also published and push those too
            # TODO: discuss: it would be more efficient to only do this if the published
            #       status itself has changed (vs. all the time anything in an already
            #       published entry was changed), but we would need to write our own
            #       update function in the serializer, to set the update_fields in kwargs
            published_media = Media.objects.filter(entry_id=instance.id, published=True, status=STATUS_CONVERTED)
            for medium in published_media:
                queue.enqueue(sync.push_medium, medium=medium, depends_on=entry_sync)
            # TODO: similar to media also relations would only have to be pushed after
            #       publishing and not on every save
            if instance.from_entries.exists():
                queue.enqueue(sync.push_relations, entry=instance, depends_on=entry_sync)
            # TODO: this doesn't seem very performant, adapt Showroom API to be able
            #       to push relations in both directions
            for entry in instance.to_entries.all():
                queue.enqueue(sync.push_relations, entry=entry, depends_on=entry_sync)
        # if the instance was just created but not published, we do nothing. but if its
        # published status (now) is false and it was not just created, we have to delete
        # it from Showroom
        elif not created:
            queue.enqueue(sync.delete_entry, entry=instance)
            # TODO: discuss and implement failure handling


@receiver(post_delete, sender=Entry)
def entry_post_delete(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        if instance.published:
            queue = django_rq.get_queue('default')
            queue.enqueue(sync.delete_entry, entry=instance)
            # TODO: discuss and implement failure handling


@receiver(post_save, sender=Relation)
def relation_post_save(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        if instance.from_entry.published and instance.to_entry.published:
            queue = django_rq.get_queue('default')
            queue.enqueue(sync.push_relations, entry=instance.from_entry)
            # TODO: discuss and implement failure handling


@receiver(post_delete, sender=Relation)
def relation_post_delete(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        if instance.from_entry.published and instance.to_entry.published:
            queue = django_rq.get_queue('default')
            queue.enqueue(sync.push_relations, entry=instance.from_entry)
            # TODO: discuss and implement failure handling


@receiver(post_save, sender=Media)
def media_post_save(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        if (
            instance.published
            and instance.status == STATUS_CONVERTED
            and Entry.objects.get(pk=instance.entry_id).published
        ):
            django_rq.enqueue(sync.push_medium, medium=instance)
