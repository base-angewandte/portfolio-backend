import os

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


def get_quota_for_user(user):
    cache_key = '{}_quota'.format(user.username)
    quota = cache.get(cache_key)
    if not quota:
        joined = user.date_joined
        today = timezone.now()
        diff = today.year - joined.year - ((today.month, today.day) < (joined.month, joined.day))
        quota = settings.USER_QUOTA * (diff + 1)
        cache.set(cache_key, quota, 86400)
    return quota


def get_free_space_for_user(user):
    return get_quota_for_user(user) - get_used_space_for_user(user)


def get_used_space_for_user(user):
    path = os.path.join(settings.PROTECTED_MEDIA_ROOT, settings.HASHIDS.encode(user.id))
    size = 0
    for root, dirs, files in os.walk(path):
        size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
    return size


def check_quota(user, size):
    if get_used_space_for_user(user) + size < get_quota_for_user(user):
        return True
    return False
