import functools
import math
import os

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from PIL import Image


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


def humanize_size(size_bytes):
    if size_bytes == 0:
        return '0 B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return '{} {}'.format(s, size_name[i])


# from https://stackoverflow.com/a/30462851
def image_transpose_exif(im):
    """
    Apply Image.transpose to ensure 0th row of pixels is at the visual
    top of the image, and 0th column is the visual left-hand side.
    Return the original image if unable to determine the orientation.

    As per CIPA DC-008-2012, the orientation field contains an integer,
    1 through 8. Other values are reserved.
    """

    exif_orientation_tag = 0x0112
    exif_transpose_sequences = [                   # Val  0th row  0th col
        [],                                        # 0    (reserved)
        [],                                        # 1    top      left
        [Image.FLIP_LEFT_RIGHT],                   # 2    top      right
        [Image.ROTATE_180],                        # 3    bottom   right
        [Image.FLIP_TOP_BOTTOM],                   # 4    bottom   left
        [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],  # 5    left     top
        [Image.ROTATE_270],                        # 6    right    top
        [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],  # 7    right    bottom
        [Image.ROTATE_90],                         # 8    left     bottom
    ]

    try:
        seq = exif_transpose_sequences[im._getexif()[exif_orientation_tag]]
    except Exception:
        return im
    else:
        return functools.reduce(type(im).transpose, seq, im)
