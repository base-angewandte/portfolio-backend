import django_rq

from django.conf import settings
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from core.models import Entry, Relation
from media_server.models import STATUS_CONVERTED, Media
from media_server.signals import media_order_update

from . import sync


@receiver(post_save, sender=Entry, dispatch_uid='showroom_connector_entry_post_save')
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
            for relation in instance.to_entries.all():
                queue.enqueue(sync.push_relations, entry=relation.from_entry, depends_on=entry_sync)
        # if the instance was just created but not published, we do nothing. but if its
        # published status (now) is false and it was not just created, we have to delete
        # it from Showroom
        elif not created:
            queue.enqueue(sync.delete_entry, entry=instance)
            # TODO: discuss and implement failure handling


@receiver(post_delete, sender=Entry, dispatch_uid='showroom_connector_entry_post_delete')
def entry_post_delete(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        if instance.published:
            queue = django_rq.get_queue('default')
            queue.enqueue(sync.delete_entry, entry=instance)
            # TODO: discuss and implement failure handling


@receiver(post_save, sender=Relation, dispatch_uid='showroom_connector_relation_post_save')
def relation_post_save(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        if instance.from_entry.published and instance.to_entry.published:
            queue = django_rq.get_queue('default')
            queue.enqueue(sync.push_relations, entry=instance.from_entry)
            # TODO: discuss and implement failure handling


@receiver(post_delete, sender=Relation, dispatch_uid='showroom_connector_relation_post_delete')
def relation_post_delete(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        if instance.from_entry.published and instance.to_entry.published:
            queue = django_rq.get_queue('default')
            queue.enqueue(sync.push_relations, entry=instance.from_entry)
            # TODO: discuss and implement failure handling


@receiver(post_save, sender=Media, dispatch_uid='showroom_connector_media_post_save')
def media_post_save(sender, instance, created, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        entry = Entry.objects.get(pk=instance.entry_id)
        if entry.published:
            if instance.published:
                if instance.status == STATUS_CONVERTED:
                    django_rq.enqueue(sync.push_medium, medium=instance)
                    # TODO: discuss and implement failure handling
            elif not created:
                django_rq.enqueue(sync.delete_medium, medium=instance)
                # TODO: discuss and implement failure handling


@receiver(pre_delete, sender=Media, dispatch_uid='showroom_connector_media_pre_delete')
def media_pre_delete(sender, instance, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        # check if both the entry and the medium itself have been published, we also
        # have to sync this deletion to showroom
        if (
            instance.published
            and instance.status == STATUS_CONVERTED
            and Entry.objects.get(pk=instance.entry_id).published
        ):
            django_rq.enqueue(sync.delete_medium, medium=instance)
            # TODO: discuss and implement failure handling


@receiver(media_order_update, dispatch_uid='showroom_connector_media_order_update')
def media_order_update(sender, entry_id, *args, **kwargs):
    if settings.SYNC_TO_SHOWROOM:
        entry = Entry.objects.get(pk=entry_id)
        if entry.published:
            media = Media.objects.filter(entry_id=entry_id, published=True, status=STATUS_CONVERTED)
            queue = django_rq.get_queue('default')
            for m in media:
                queue.enqueue(sync.push_medium, medium=m)
                # TODO: discuss and implement failure handling
