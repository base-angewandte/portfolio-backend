from django.conf import settings
from django.core.cache import cache
from django.utils.functional import lazy
from django.utils.translation import get_language
from requests import RequestException
from skosmos_client import SkosmosClient

skosmos = SkosmosClient(api_base=settings.SKOSMOS_API)


def get_uri(concept):
    return '{}{}'.format(settings.PORTFOLIO_GRAPH, concept)


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
                pass
        except RequestException:
            pass

        if label:
            cache.set(cache_key, label, 86400)  # 1 day

    return label or ''


get_preflabel_lazy = lazy(get_preflabel, str)
