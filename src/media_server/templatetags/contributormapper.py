import logging
from collections import defaultdict

from django import template

from core.skosmos import get_equivalent_concepts

register = template.Library()


@register.filter(name='contributors_by_role')
def contributors_by_role(contributors):
    """Fetches the contributors as a roles."""
    if contributors is None:
        """Bail early on no contributors: contributors is None and not [] if
        there none."""
        return []
    ROLE_MAP = {}
    roles = defaultdict(list)
    for c in contributors:
        for role in c['roles']:
            if not role.get('source', ''):
                continue
            if role['source'] not in ROLE_MAP:
                # cache the eq role lookup
                eq_roles = get_equivalent_concepts(role['source'])[0]
                try:
                    phaidra_role = [r.get('uri') for r in eq_roles if 'loc.gov' in r.get('uri')][0]
                    # WARNING: If one contributor role is mapped to
                    # more than one MARC role this will choose the first value
                except IndexError:
                    logging.warning(
                        'Contributor role %s has no equivalent MARC role in %s',
                        role['source'],
                        eq_roles,
                    )
                    continue  # no MARC role found, skip

                ROLE_MAP[role['source']] = phaidra_role

            roles[ROLE_MAP[role['source']]].append({'source': c.get('source', ''), 'label': c.get('label', '')})

    return [{k: v} for k, v in roles.items()]


@register.filter(name='phaidra_role_code')
def phaidra_role_code(arg):
    """Returns the role "key" as used in Phaidra-JSON LD."""
    return f'role:{arg.split("/")[-1]}'
