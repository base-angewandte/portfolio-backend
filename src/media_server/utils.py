import os

from django.conf import settings


def get_used_space_for_user(user):
    path = os.path.join(settings.PROTECTED_MEDIA_ROOT, settings.HASHIDS.encode(user.id))
    size = 0
    for root, dirs, files in os.walk(path):
        size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
    return size


def check_quota(user, size):
    if get_used_space_for_user(user) + size < settings.USER_QUOTA:
        return True
    return False
