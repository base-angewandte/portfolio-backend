import unicodedata

from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _

placeholder_lazy = lazy(lambda label: _('Enter %(label)s') % {'label': label}, str)


def unaccent(text):
    return str(unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8'))
