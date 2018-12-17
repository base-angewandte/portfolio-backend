from django.conf import settings
from django.core.cache import cache
from django.utils.functional import lazy
from django.utils.translation import get_language
from skosmos_client import SkosmosClient

skosmos = SkosmosClient(api_base=settings.SKOSMOS_API)


def get_preflabel(concept):
    language = get_language() or 'en'
    cache_key = 'get_preflabel_{}_{}'.format(language, concept)

    label = cache.get(cache_key)
    if not label:
        c = skosmos.get_concept(settings.PORTFOLIO_VOCID, '{}{}'.format(settings.PORTFOLIO_GRAPH, concept))
        try:
            label = c.label(language)
        except KeyError:
            try:
                label = c.label('en' if language == 'de' else 'de')
            except KeyError:
                label = ''
        if label:
            cache.set(cache_key, label, 1000)

    return label


get_preflabel_lazy = lazy(get_preflabel, str)
