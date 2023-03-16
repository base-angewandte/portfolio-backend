"""# Tests to reproduce https://basedev.uni-ak.ac.at/redmine/issues/1504

> As discussed in Improvement #1330, Veronika has prepared the mapping of the different "roles" in Portfolio to MARC
> Code List for Relators Scheme.
> Yet, most of this mapping won't show up in Phaidra; e.g.:

>    http://base.uni-ak.ac.at/portfolio/vocabulary/visual_surrogates
>    http://base.uni-ak.ac.at/portfolio/vocabulary/architecture
>    http://base.uni-ak.ac.at/portfolio/vocabulary/commissions_orders_for_works
>    http://base.uni-ak.ac.at/portfolio/vocabulary/stage_lighting

According to Christoph Hoffmann, only library of congress roles are accepted, see:
Oldest implementation I know of:
Commit: 67748c5d3b93e4085d74a0a48e6e01066303eaa4
Location: src/media_server/templatetags/contributormapper.py:28
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

import django_rq
import requests

from django.test import TestCase

from media_server.archiver.implementations.phaidra.metadata.archiver import ThesisMetadataArchiver
from media_server.archiver.implementations.phaidra.phaidra_tests.utilities import ClientProvider, ModelProvider
from media_server.archiver.interface.archiveobject import ArchiveObject

if TYPE_CHECKING:
    from core.models import Entry
    from media_server.models import Media


def get_skosmos_same_as_roles(portfolio_role_url: str) -> set[str]:
    """Testing utility function to retrieve the same as roles from skosmos.

    :param portfolio_role_url: A valid url like http://base.uni-ak.ac.at/portfolio/vocabulary/visual_surrogates
    :return: A list of same as role codes
    """
    params = {'uri': portfolio_role_url, 'format': 'application/ld+json'}
    response = requests.get('https://voc.uni-ak.ac.at/skosmos/rest/v1/povoc/data', params=params)
    if response.status_code != 200:
        raise RuntimeError(f'Skosmos response status not 200, but {response.status_code} with message {response.text}')
    data = response.json()
    graph = data['graph']
    for node in graph:
        if node['uri'] == portfolio_role_url:
            if 'owl:sameAs' not in node:
                owl_sameAs = set()
            elif node['owl:sameAs'].__class__ is dict:
                owl_sameAs = set(node['owl:sameAs'].values())
            elif node['owl:sameAs'].__class__ is list:
                owl_sameAs = {element['uri'] for element in node['owl:sameAs']}
            else:
                raise RuntimeError(f'Type of node not supported: {node.__class__}')
            regex = re.compile(r'(http://id.loc.gov/vocabulary/relators/)([a-z)]{3})')
            matches = {regex.match(same_as) for same_as in owl_sameAs}
            return {match.group(2) for match in matches if match}

    else:
        raise RuntimeError(f'Did not find {portfolio_role_url} in graph nodes')


def get_phaidra_same_as_roles(entry: Entry) -> set[str]:
    url = f'https://services.phaidra-sandbox.univie.ac.at/api/object/{entry.archive_id}/jsonld'
    response = requests.get(url)
    if response.status_code != 200:
        raise RuntimeError(
            f'Phaidra response <{url}> status not 200, but {response.status_code} with message {response.text}'
        )
    data: dict = response.json()
    role_regex = re.compile(r'(role:)([a-z]{3,})')
    matches = [role_regex.match(key) for key, value in data.items()]
    roles = {match.group(2) for match in matches if match}
    # filter out static roles:
    return roles.difference(
        {
            # Check src/media_server/archiver/implementations/phaidra/metadata/thesis/schemas.py
            'supervisor',
            # src/media_server/archiver/implementations/phaidra/metadata/default/schemas.py
            'edt',
            'pbl',
            'aut',
        }
    )


class RoleMappingTestCase(TestCase):
    def _get_archived_entry_with_role_and_media(self, role_uri: str) -> tuple[Entry, Media]:
        self.model_provider = ModelProvider()
        entry = self.model_provider.get_entry()
        entry.data['contributors'].append(
            {
                'label': 'Universität für Angewandte Kunst Wien',
                'roles': [
                    {
                        'label': {'de': 'Ma wurscht', 'en': 'Don\'t give a shit'},
                        'source': role_uri,
                    }
                ],
            },
        )
        entry.save()
        media = self.model_provider.get_media(entry)
        client_provider = ClientProvider(self.model_provider)
        response = client_provider.get_media_primary_key_response(media, only_validate=False)
        if response.status_code != 200:
            raise RuntimeError(f'Failed to archive media {response} {response.content}')
        worker = django_rq.get_worker('high')
        worker.work(burst=True)  # wait until it is done
        entry.refresh_from_db()
        media.refresh_from_db()
        return entry, media

    def test_visual_surrogates_phaidra(self):
        role = 'http://base.uni-ak.ac.at/portfolio/vocabulary/visual_surrogates'
        entry, _ = self._get_archived_entry_with_role_and_media(role)
        skosmos_mapping = get_skosmos_same_as_roles(role)
        phaidra_result = get_phaidra_same_as_roles(entry)
        self.assertEqual(set(), skosmos_mapping.difference(phaidra_result))

    def test_visual_surrogates_schema(self):
        role = 'http://base.uni-ak.ac.at/portfolio/vocabulary/visual_surrogates'
        entry, media = self._get_archived_entry_with_role_and_media(role)
        skosmos_mapping = get_skosmos_same_as_roles(role)
        archiver = ThesisMetadataArchiver(
            archive_object=ArchiveObject(
                self.model_provider.user,
                media_objects={
                    media,
                },
                entry=entry,
            )
        )
        archiver.validate()
        regex = re.compile(r'(role:)([a-z]{3,})')
        translated_roles = [regex.match(key) for key in archiver.data['metadata']['json-ld'].keys()]
        translated_roles = [match.group(2) for match in translated_roles if match]
        self.assertEqual(set(), skosmos_mapping.difference(translated_roles))
