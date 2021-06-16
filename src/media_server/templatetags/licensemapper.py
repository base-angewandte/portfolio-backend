from django import template

from core.skosmos import get_equivalent_concepts

register = template.Library()


@register.filter(name='phaidra_eq_license')
def phaidra_eq_license(arg):
    """Fetches the equivalent concept for Portfolio license to be mapped to
    Phaidra."""
    eq_concepts = get_equivalent_concepts(arg)
    if eq_concepts:
        # FIXME: What happens if there are more than in equivalent concepts?
        return eq_concepts[0].get('uri', arg)

    # FIXME: Rely on static mapping if something foes wrong?
    return arg
