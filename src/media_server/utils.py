import math
import os

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


def user_hash(username):
    return settings.HASHIDS.encode_hex(username.encode('utf-8').hex())


def decode_user_hash(hash):
    return bytes.fromhex(settings.HASHIDS.decode_hex(hash)).decode('utf-8')


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
    return max(get_quota_for_user(user) - get_used_space_for_user(user), 0)


def get_used_space_for_user(user):
    path = os.path.join(settings.PROTECTED_MEDIA_ROOT, user_hash(user.username))
    size = 0
    for root, _dirs, files in os.walk(path):
        size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
    return size


def check_quota(user, size):
    if get_used_space_for_user(user) + size < get_quota_for_user(user):
        return True
    return False


def humanize_size(size_bytes):
    if size_bytes == 0:
        return '0 B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return '{} {}'.format(s, size_name[i])
