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


def convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format
    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)
