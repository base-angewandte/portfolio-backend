from django import template

from core.skosmos import get_equivalent_concepts

register = template.Library()


@register.filter(name='contributors_by_role')
def contributors_by_role(arg):
    """Fetches the contributors as a roles"""
    print(arg)
    return ''
