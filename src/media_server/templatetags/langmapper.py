from django import template

register = template.Library()


@register.filter(name='three_letter_lang')
def three_letter_lang(arg):
    """Converts the given string to a three letter language code."""
    if arg.endswith('en'):
        return 'eng'
    if arg.endswith('de'):
        return 'deu'

    return arg
