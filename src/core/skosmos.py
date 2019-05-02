from django.conf import settings
from django.core.cache import cache
from django.utils.functional import lazy
from django.utils.translation import get_language
from requests import RequestException
from rdflib.namespace import SKOS
from skosmos_client import SkosmosClient

skosmos = SkosmosClient(api_base=settings.SKOSMOS_API)


def get_languages():
    language = get_language() or 'en'
    cache_key_languages = 'get_languages_{}'.format(language)
    cache_key_languages_labels = 'get_languages_labels_{}'.format(language)

    languages = cache.get(cache_key_languages, [])
    languages_labels = cache.get(cache_key_languages_labels, [])

    if not languages or not languages_labels:
        r = skosmos.top_concepts(settings.LANGUAGES_VOCID, lang=language)

        r = sorted(r, key=lambda k: k['label'])

        for l in r:
            languages.append(l['uri'])
            languages_labels.append(l['label'])

        if languages:
            cache.set(cache_key_languages, languages, 86400)  # 1 day
        if languages_labels:
            cache.set(cache_key_languages_labels, languages_labels, 86400)  # 1 day

    return languages, languages_labels


def get_uri(concept, graph=settings.VOC_GRAPH):
    return '{}{}'.format(graph, concept)


def get_altlabel(concept, project=settings.VOC_ID, graph=settings.VOC_GRAPH):
    language = get_language() or 'en'
    cache_key = 'get_altlabel_{}_{}'.format(language, concept)

    label = cache.get(cache_key)
    if not label:
        try:
            g = skosmos.data('{}{}'.format(graph, concept))
            for uri, l in g.subject_objects(SKOS.altLabel):
                if l.language == language:
                    label = l
                    break
        except RequestException:
            pass

        if label:
            cache.set(cache_key, label, 86400)  # 1 day

    return label or get_preflabel(concept, project, graph)


def get_preflabel(concept, project=settings.VOC_ID, graph=settings.VOC_GRAPH):
    language = get_language() or 'en'
    cache_key = 'get_preflabel_{}_{}'.format(language, concept)

    label = cache.get(cache_key)
    if not label:
        c = skosmos.get_concept(project, '{}{}'.format(graph, concept))
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


def get_collection_members(collection, maxhits=1000, use_cache=True):
    cache_key = 'get_collection_members_{}'.format(collection)

    members = cache.get(cache_key) if use_cache else None
    if not members:
        m = skosmos.search(query='*', group=collection, maxhits=maxhits, lang='en')
        members = [i['uri'] for i in m]

        if members:
            cache.set(cache_key, members, 86400)  # 1 day

    return members or []


get_altlabel_lazy = lazy(get_altlabel, str)
get_preflabel_lazy = lazy(get_preflabel, str)
