from django.utils.functional import lazy
from django.utils.translation import get_language

get_language_lazy = lazy(get_language, str)


def boolean_input(question, default=None):
    result = input('{} '.format(question))
    if not result and default is not None:
        return default
    while not result or result[0].lower() not in 'yn':
        result = input('Please answer yes or no: ')
    return result[0].lower() == 'y'
