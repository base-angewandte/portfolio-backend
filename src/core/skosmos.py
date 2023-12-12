import hashlib

import requests
from rdflib.namespace import SKOS
from requests import RequestException
from skosmos_client import SkosmosClient

from django.conf import settings
from django.core.cache import cache
from django.utils.functional import lazy
from django.utils.translation import get_language

from .utils import unaccent

CACHE_TIME = 86400  # 1 day

PROJECT_MAPPING = {
    'http://base.uni-ak.ac.at/portfolio/languages/': 'languages',
    'http://base.uni-ak.ac.at/recherche/keywords/': 'basekw',
    'http://base.uni-ak.ac.at/vocabulary/': 'basevoc',
    'http://base.uni-ak.ac.at/portfolio/licenses/': 'licenses',
    'http://base.uni-ak.ac.at/portfolio/taxonomy/': 'potax',
    'http://base.uni-ak.ac.at/portfolio/vocabulary/': 'povoc',
    'http://base.uni-ak.ac.at/portfolio/disciplines/': 'disciplines',
}

skosmos = SkosmosClient(api_base=settings.SKOSMOS_API)


def autosuggest(data, query, language=None):
    if not language:
        language = get_language() or 'en'

    query = unaccent(query.lower())

    result = list(
        filter(
            lambda d: query
            in unaccent(d['label'].get(language, d['label'].get('en', '')).lower()),
            data,
        )
    )

    return result


def get_json_data(uri, vocid=None):
    payload = {'uri': uri, 'format': 'application/ld+json'}

    if vocid is not None:
        url = settings.SKOSMOS_API + vocid + '/data'
    else:
        url = settings.SKOSMOS_API + 'data'

    req = requests.get(
        url,
        params=payload,
        timeout=settings.REQUESTS_TIMEOUT,
    )
    req.raise_for_status()

    return req.json()


def get_search_data(uri):
    payload = {
        'query': '*',
        'parent': uri,
        'fields': 'prefLabel',
        'lang': 'en',
        'maxhits': 1000,
        'unique': 'true',
    }

    req = requests.get(
        settings.SKOSMOS_API + 'search',
        params=payload,
        timeout=settings.REQUESTS_TIMEOUT,
    )
    req.raise_for_status()
    return req.json()['results']


def fetch_data(uri, vocid=None, fetch_children=False, source_name=None):
    language = get_language() or 'en'

    cache_key = hashlib.md5(  # nosec
        '_'.join(
            [uri, vocid or '', str(fetch_children), source_name or '', language]
        ).encode('utf-8')
    ).hexdigest()

    data = cache.get(cache_key, [])

    if not data:
        d = get_json_data(uri, vocid)

        for i in d['graph']:
            if i.get('type') == 'skos:Concept' and i['uri'] != uri:
                md = {'source': i['uri']}
                if isinstance(i['prefLabel'], list):
                    md['label'] = {d['lang']: d['value'] for d in i['prefLabel']}
                else:
                    md['label'] = {i['prefLabel']['lang']: i['prefLabel']['value']}
                if source_name:
                    md['source_name'] = source_name
                data.append(md)

                if fetch_children:
                    cd = get_search_data(i['uri'])
                    for ci in cd:
                        cmd = {'source': ci['uri'], 'label': ci['prefLabels']}
                        if source_name:
                            cmd['source_name'] = source_name
                        data.append(cmd)

        if data:
            data = sorted(
                data,
                key=lambda x: x.get('label', {})
                .get(language, x.get('label', {}).get('en', 'zzz'))
                .lower(),
            )
            cache.set(cache_key, data, CACHE_TIME)

    return data


def get_base_keywords():
    return fetch_data(
        'http://base.uni-ak.ac.at/recherche/keywords/collection_base',
        source_name='base',
    )


def get_disciplines():
    cache_key = 'get_disciplines'

    data = cache.get(cache_key, [])

    if not data:
        data = list(
            filter(
                lambda x: len(x['source'].split('/')[-1]) % 3 == 0,
                fetch_data(
                    'http://base.uni-ak.ac.at/portfolio/disciplines/oefos',
                    fetch_children=True,
                    source_name='voc',
                ),
            )
        )

        if data:
            cache.set(cache_key, data, CACHE_TIME)

    return data


def get_formats():
    return fetch_data('http://base.uni-ak.ac.at/portfolio/vocabulary/format_type')


def get_keywords():
    return [
        *get_base_keywords(),
        *get_disciplines(),
    ]


def get_languages():
    return fetch_data('http://base.uni-ak.ac.at/portfolio/languages/iso_639_1')


def get_languages_choices():
    language = get_language() or 'en'
    cache_key_languages = f'get_languages_{language}'
    cache_key_languages_labels = f'get_languages_labels_{language}'

    languages = cache.get(cache_key_languages, [])
    languages_labels = cache.get(cache_key_languages_labels, [])

    if not languages or not languages_labels:
        r = skosmos.top_concepts(settings.LANGUAGES_VOCID, lang=language)

        r = sorted(r, key=lambda k: k['label'].lower())

        for lang in r:
            languages.append(lang['uri'])
            languages_labels.append(lang['label'])

        if languages:
            cache.set(cache_key_languages, languages, CACHE_TIME)
        if languages_labels:
            cache.set(cache_key_languages_labels, languages_labels, CACHE_TIME)

    return languages, languages_labels


def get_materials():
    return fetch_data('http://base.uni-ak.ac.at/portfolio/vocabulary/material_type')


def get_media_licenses():
    return fetch_data(
        'http://base.uni-ak.ac.at/portfolio/licenses/collection_media_licenses'
    )


def get_roles():
    return fetch_data('http://base.uni-ak.ac.at/portfolio/vocabulary/role')


def get_statuses():
    return fetch_data(
        'http://base.uni-ak.ac.at/vocabulary/collection_portfolio_project_status'
    )


def get_software_licenses():
    return fetch_data(
        'http://base.uni-ak.ac.at/portfolio/licenses/collection_software_licenses'
    )


def get_text_types():
    return fetch_data('http://base.uni-ak.ac.at/portfolio/vocabulary/text_type')


def get_entry_types():
    cache_key = 'get_entry_types'

    data = cache.get(cache_key, [])

    if not data:
        from .schemas import ACTIVE_TYPES

        data = list(
            filter(
                lambda x: x['source'] in ACTIVE_TYPES,
                fetch_data(
                    'http://base.uni-ak.ac.at/portfolio/taxonomy/portfolio_taxonomy'
                ),
            )
        )

        if data:
            cache.set(cache_key, data, CACHE_TIME)

    return data


def get_uri(concept, graph=settings.VOC_GRAPH):
    return f'{graph}{concept}'


def get_altlabel(concept, project=settings.VOC_ID, graph=settings.VOC_GRAPH, lang=None):
    if lang:
        language = lang
    else:
        language = get_language() or 'en'
    cache_key = f'get_altlabel_{language}_{concept}'

    label = cache.get(cache_key)
    if not label:
        try:
            g = skosmos.data(f'{graph}{concept}')
            for _uri, l in g.subject_objects(SKOS.altLabel):
                if l.language == language:
                    label = l
                    break
        except RequestException:
            pass

    label = label or get_preflabel(concept, project, graph, language)

    if label:
        cache.set(cache_key, label, CACHE_TIME)

    return label


def get_altlabel_collection(
    collection, project=settings.TAX_ID, graph=settings.TAX_GRAPH, lang=None
):
    return (
        get_altlabel(collection, project, graph, lang)
        .replace('Sammlung', '')
        .replace('Collection', '')
        .replace('JART', '')
        .replace('INDEX', '')
        .strip()
    )


def get_preflabel(
    concept, project=settings.VOC_ID, graph=settings.VOC_GRAPH, lang=None
):
    if lang:
        language = lang
    else:
        language = get_language() or 'en'
    cache_key = f'get_preflabel_{project}_{language}_{concept}'

    label = cache.get(cache_key)
    if not label:
        c = skosmos.get_concept(project, f'{graph}{concept}')
        try:
            label = c.label(language)
        except KeyError:
            try:
                label = c.label('de' if language == 'en' else 'en')
            except KeyError:
                pass
        except RequestException:
            pass

        if label:
            cache.set(cache_key, label, CACHE_TIME)

    return label or ''


def get_preflabel_via_uri(concept, lang=None):
    g, c = concept.rsplit('/', 1)
    g += '/'
    return get_preflabel(c, project=PROJECT_MAPPING[g], graph=g, lang=lang)


def get_collection_members(collection, maxhits=1000, use_cache=True):
    cache_key = f'get_collection_members_{collection}'

    members = cache.get(cache_key) if use_cache else None
    if not members:
        m = skosmos.search(query='*', group=collection, maxhits=maxhits, lang='en')
        members = [i['uri'] for i in m]

        if members:
            cache.set(cache_key, members, CACHE_TIME)

    return members or []


get_altlabel_lazy = lazy(get_altlabel, str)
get_preflabel_lazy = lazy(get_preflabel, str)
