from django.utils.functional import lazy
from django.utils.translation import get_language

get_language_lazy = lazy(get_language, str)
