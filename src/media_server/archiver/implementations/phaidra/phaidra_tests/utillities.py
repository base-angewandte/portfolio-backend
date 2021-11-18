import typing
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Set

from rest_framework.test import APIClient

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Entry
from media_server.models import Media

if TYPE_CHECKING:
    from rest_framework.response import Response


class PhaidraContainerGenerator:
    title: str = 'Title'

    base = {
        'dcterms:type': [
            {
                '@type': 'skos:Concept',
                'skos:exactMatch': ['https://pid.phaidra.org/vocabulary/8MY0-BQDQ'],
                'skos:prefLabel': [{'@language': 'eng', '@value': 'container'}],
            }
        ],
        'edm:hasType': [
            {
                '@type': 'skos:Concept',
                'skos:prefLabel': [
                    {
                        '@value': 'Master-Arbeit',
                        '@language': 'deu',
                    },
                    {
                        '@value': 'master thesis',
                        '@language': 'eng',
                    },
                ],
                'skos:exactMatch': [
                    'http://base.uni-ak.ac.at/portfolio/taxonomy/master_thesis',
                ],
            }
        ],
        'dce:title': [
            {
                '@type': 'bf:Title',
                'bf:mainTitle': [{'@value': title, '@language': 'und'}],
            }
        ],
        'dcterms:language': [],
        'dcterms:subject': [],
        'rdau:P60048': [],
        'dce:format': [],
        'bf:note': [],
        'role:edt': [],
        'role:aut': [],
        'role:pbl': [],
    }

    author = {
        '@type': 'schema:Person',
        'skos:exactMatch': [
            {
                '@value': 'http://d-nb.info/gnd/5299671-2',
                '@type': 'ids:uri',
            },
        ],
        'schema:name': [
            {
                '@value': 'Universität für Angewandte Kunst Wien',
            }
        ],
    }

    language = {
        '@type': 'skos:Concept',
        'skos:prefLabel': [{'@value': 'Akan', '@language': 'eng'}, {'@value': 'Akan-Sprache', '@language': 'deu'}],
        'skos:exactMatch': ['http://base.uni-ak.ac.at/portfolio/languages/ak'],
    }

    supervisor = {
        '@type': 'schema:Person',
        'skos:exactMatch': [
            {
                '@value': 'http://d-nb.info/gnd/5299671-2',
                '@type': 'ids:uri',
            },
        ],
        'schema:name': [
            {
                '@value': 'Universität für Angewandte Kunst Wien',
            }
        ],
    }

    english_abstract = {
        '@type': 'bf:Summary',
        'skos:prefLabel': [
            {
                '@value': 'Abstract',
                '@language': 'eng',
            },
        ],
    }

    german_abstract = {
        '@type': 'bf:Summary',
        'skos:prefLabel': [
            {
                '@value': 'Abstract',
                '@language': 'deu',
            },
        ],
    }

    @classmethod
    def create_phaidra_container(
        cls,
        respect_author_rule: bool = True,
        respect_language_rule: bool = True,
        respect_supervisor_role: bool = True,
        respect_english_abstract_rule: bool = True,
        respect_german_abstract_rule: bool = True,
    ) -> dict:
        phaidra_container = deepcopy(cls.base)
        if respect_author_rule:
            phaidra_container['role:aut'].append(cls.author)
        if respect_language_rule:
            phaidra_container['dcterms:language'].append(cls.language)

        if respect_supervisor_role:
            if 'role:dgs' not in phaidra_container:
                phaidra_container['role:dgs'] = []
            phaidra_container['role:dgs'].append(cls.supervisor)

        if respect_english_abstract_rule:
            if 'bf:note' not in phaidra_container:
                phaidra_container['bf:note'] = []
            phaidra_container['bf:note'].append(cls.english_abstract)

        if respect_german_abstract_rule:
            if 'bf:note' not in phaidra_container:
                phaidra_container['bf:note'] = []
            phaidra_container['bf:note'].append(cls.german_abstract)

        return {'metadata': {'json-ld': phaidra_container}}


class ModelProvider:
    def __init__(self):
        self.username = 'Φαίδρα'
        self.peeword = 'peeword'  # Yes, I am trying to trick some git hook …
        try:
            self.user = User.objects.create_user(username=self.username, password=self.peeword)
        except IntegrityError:
            self.user = User.objects.get_by_natural_key(username=self.username)

    def get_media(
        self, entry: 'Entry', license_: bool = True, mime_type: Optional[str] = 'text/plain', file_type='pdf'
    ) -> 'Media':
        media = Media(
            owner=self.user,
            file=SimpleUploadedFile(f'example.{file_type}', b'example file'),
            entry_id=entry.id,
        )
        if mime_type:
            media.mime_type = mime_type
        if license_:
            media.license = {
                'label': {'en': 'Creative Commons Attribution 4.0'},
                'source': 'http://base.uni-ak.ac.at/portfolio/licenses/CC-BY-4.0',
            }

        media.save()
        return media

    def get_entry(
        self,
        title: bool = True,
        type_: bool = True,
        author: bool = True,
        german_language: bool = True,
        supervisor: bool = True,
        english_abstract: bool = True,
        german_abstract: bool = True,
        french_abstract: bool = False,
        akan_language: bool = False,
        thesis_type: bool = True,
    ) -> 'Entry':
        """
        :param thesis_type: if to use thesis type, or else. Only will be applied if type_ is True
        :param title: Mandatory field
        :param type_: Mandatory field
        :param author: Mandatory field
        :param german_language: Mandatory field
        :param supervisor: Mandatory field
        :param english_abstract: Mandatory field
        :param german_abstract: Mandatory field
        :param french_abstract: Obligatory field
        :param akan_language: Not Implemented field
        :param german_language: Obligatory field
        :return:
        """
        entry = Entry(owner=self.user, data={})
        entry.update_archive = False
        if title:
            entry.title = 'A Title'
        if type_:
            if thesis_type:
                entry.type = {
                    'label': {'de': 'Masterarbeit', 'en': 'master thesis'},
                    'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/master_thesis',
                }
            else:
                entry.type = {
                    'label': {'de': 'Installation', 'en': 'Installation'},
                    'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/installation',
                }

        entry.data['authors'] = []
        if author:
            entry.data['authors'].append(
                {
                    'label': 'Universität für Angewandte Kunst Wien',
                    'roles': [
                        {
                            'label': {'de': 'Autor*in', 'en': 'Author'},
                            'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/author',
                        }
                    ],
                    'source': 'http://d-nb.info/gnd/5299671-2',
                }
            )

        if german_language:
            entry.data['language'] = [
                {
                    'label': {
                        'de': 'Deutsch',
                        'en': 'German',
                    },
                    'source': 'http://base.uni-ak.ac.at/portfolio/languages/de',
                }
            ]

        if supervisor:
            if 'contributors' not in entry.data:
                entry.data['contributors'] = []

            entry.data['contributors'].append(
                {
                    'label': 'Universität für Angewandte Kunst Wien',
                    'roles': [
                        {
                            'label': {'de': 'Supervisor', 'en': 'supervisor'},
                            'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor',
                        }
                    ],
                },
            )

        if english_abstract:
            if entry.texts is None:
                entry.texts = []
            entry.texts.append(
                {
                    'data': [
                        {'text': 'Abstract', 'language': {'source': 'http://base.uni-ak.ac.at/portfolio/languages/en'}}
                    ],
                    'type': {
                        'label': {'de': 'Abstract', 'en': 'Abstract'},
                        'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract',
                    },
                }
            )

        if german_abstract:
            if entry.texts is None:
                entry.texts = []
            entry.texts.append(
                {
                    'data': [
                        {'text': 'Abstract', 'language': {'source': 'http://base.uni-ak.ac.at/portfolio/languages/de'}}
                    ],
                    'type': {
                        'label': {'de': 'Abstract', 'en': 'Abstract'},
                        'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract',
                    },
                }
            )

        if french_abstract:
            if entry.texts is None:
                entry.texts = []
            entry.texts.append(
                {
                    'data': [
                        {'text': 'Abstract', 'language': {'source': 'http://base.uni-ak.ac.at/portfolio/languages/fr'}}
                    ],
                    'type': {
                        'label': {'de': 'Abstract', 'en': 'Abstract'},
                        'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract',
                    },
                }
            )

        if akan_language:
            if entry.data is None:
                entry.data = {}
            if 'language' not in entry.data:
                entry.data['language'] = []
            entry.data['language'].append(
                {
                    'label': {'de': 'Akan-Sprache', 'en': 'Akan', 'fr': 'akan'},
                    'source': 'http://base.uni-ak.ac.at/portfolio/languages/ak',
                }
            )

        entry.save()
        return entry


class ClientProvider:
    def __init__(self, model_provider: 'ModelProvider'):
        self.client = APIClient()
        r = self.client.login(username=model_provider.username, password=model_provider.peeword)
        if not r:
            raise RuntimeError('login fail')

    def get_media_primary_key_response(self, media: 'Media', only_validate: bool = True) -> 'Response':
        action = 'validate' if only_validate else 'archive'
        return self.client.get(
            f'/api/v1/{action}_assets/media/{media.id}/',
        )

    def get_multiple_medias_primary_key_response(self, medias: Set['Media'], only_validate: bool = True) -> 'Response':
        action = 'validate' if only_validate else 'archive'
        media_keys = ','.join([media.id for media in medias])
        return self.client.get(
            f'/api/v1/{action}_assets/media/{media_keys}/',
        )

    def __del__(self):
        self.client.logout()  # Very important! ;-)

    def get_update_entry_archival_response(self, entry: 'Entry') -> 'Response':
        return self.client.put(f'/api/v1/archive?entry={entry.id}')

    def get_is_changed_response(
        self,
        entry: 'Entry',
        entry_threshold: Optional[int] = None,
        asset_threshold: Optional[int] = None,
    ):
        url = f'/api/v1/archive/is-changed?entry={entry.id}'
        if entry_threshold is not None:
            url += f'&entry_threshold={entry_threshold}'
        if asset_threshold is not None:
            url += f'&asset_threshold={asset_threshold}'
        return self.client.get(url)


@dataclass
class FakeConceptMapper:
    """Fake-Map an concept (uri) to others from skosmos."""

    '''Base uri, eg https://voc.uni-ak.ac.at/skosmos/povoc/en/page/advisor'''
    uri: str

    '''comparables, eg  {'http://vocab.getty.edu/aat/300160216', 'http://d-nb.info/gnd/4005565-6'}'''
    owl_sameAs: typing.Set[str]

    class Utils:
        fakes = {
            'http://voc.uni-ak.ac.at/skosmos/povoc/en/page/another-role': {'http://id.loc.gov/vocabulary/relators/csl'},
            'http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor': {'http://id.loc.gov/vocabulary/relators/dgs'},
            'http://base.uni-ak.ac.at/portfolio/vocabulary/author': {'http://id.loc.gov/vocabulary/relators/aut'}
        }

    @classmethod
    def from_base_uri(cls, uri: str) -> 'FakeConceptMapper':
        return cls(
            uri=uri,
            owl_sameAs=cls.Utils.fakes[uri]
        )

    def to_dict(self) -> dict:
        return {
            'uri': self.uri,
            'owl:sameAs': self.owl_sameAs,
        }


@dataclass
class FakeBidirectionalConceptsMapper:
    concept_mappings: typing.Dict[str, FakeConceptMapper] = field(default_factory=dict)

    @classmethod
    def from_base_uris(cls, uris: typing.Set[str]) -> 'FakeBidirectionalConceptsMapper':
        return cls(concept_mappings={uri: FakeConceptMapper.from_base_uri(uri) for uri in uris})

    def get_owl_sameAs_from_uri(self, uri: str) -> typing.Set[str]:
        return self.concept_mappings[uri].owl_sameAs

    def get_uris_from_owl_sameAs(self, owl_sameAs: str) -> typing.Set[str]:
        return {
            uri for uri, concept_mapper in self.concept_mappings.items() if owl_sameAs in concept_mapper.owl_sameAs
        }

    def add_uri(self, uri: str) -> 'FakeBidirectionalConceptsMapper':
        if uri not in self.concept_mappings:
            self.concept_mappings[uri] = FakeConceptMapper.from_base_uri(uri)
        return self

    def add_uris(self, uris: typing.Iterable[str]) -> 'FakeBidirectionalConceptsMapper':
        for uri in uris:
            self.add_uri(uri)
        return self

    @classmethod
    def from_entry(cls, entry: 'Entry') -> 'FakeBidirectionalConceptsMapper':
        if (entry.data is None) or ('contributors' not in entry.data):
            return cls.from_base_uris(set())
        contributors = entry.data['contributors']
        roles = []
        for contributor in contributors:
            if 'roles' in contributor:
                for role in contributor['roles']:
                    if 'source' in role:
                        roles.append(role['source'])
        return cls.from_base_uris(set(roles))


def add_other_role(entry: 'Entry') -> 'Entry':
    if 'contributors' not in entry.data:
        entry.data['contributors'] = []

    entry.data['contributors'].append(
        {
            'label': 'Universität für Angewandte Kunst Wien',
            'roles': [
                {
                    'label': {'de': 'Supervisor', 'en': 'supervisor'},
                    'source': 'http://voc.uni-ak.ac.at/skosmos/povoc/en/page/another-role',
                }
            ],
        },
    )
    entry.save()
    entry.refresh_from_db()
    return entry


def add_other_phaidra_role(data: dict) -> dict:
    data['metadata']['json-ld']['role:csl'] = [
        {
            '@type': 'schema:Person',
            'skos:exactMatch': [
                {
                    '@value': 'http://voc.uni-ak.ac.at/skosmos/povoc/en/page/another-role',
                    '@type': 'ids:uri'
                },
            ],
            'schema:name': [
                {
                    '@value': 'Universität für Angewandte Kunst Wien',
                },
            ]
        }
    ]
    return data
