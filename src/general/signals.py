from django_cas_ng.signals import cas_user_authenticated

from django.conf import settings
from django.dispatch import receiver


@receiver(cas_user_authenticated, dispatch_uid="process_user_attributes")
def process_user_attributes(sender, user, created, attributes, *args, **kwargs):
    if not user:
        return

    if user.username in settings.SUPERUSERS:
        user.is_staff = True
        user.is_superuser = True
        user.save()
    else:
        user.is_staff = False
        user.is_superuser = False
        user.save()
