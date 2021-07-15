from copy import deepcopy
from typing import TYPE_CHECKING

from rest_framework.test import APIClient

from django.contrib.auth.models import User
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

    @classmethod
    def create_phaidra_container(cls, respect_author_rule: bool = True, respect_language_rule: bool = True) -> dict:
        phaidra_container = deepcopy(cls.base)
        if respect_author_rule:
            phaidra_container['role:aut'].append(cls.author)
        if respect_language_rule:
            phaidra_container['dcterms:language'].append(cls.language)

        return phaidra_container


class ModelProvider:
    def __init__(self):
        self.username = 'Φαίδρα'
        self.peeword = 'peeword'  # Yes, I am trying to trick some git hook …
        self.user = User.objects.create_user(username=self.username, password=self.peeword)

    def get_media(
        self,
        title: bool = True,
        type_: bool = True,
        license_: bool = True,
        mime_type: bool = True,
        author: bool = True,
        language: bool = True,
    ) -> 'Media':
        entry = Entry(owner=self.user, data={})
        if title:
            entry.title = 'A Title'
        if type_:
            entry.type = {
                'label': {'de': 'Masterarbeit', 'en': 'master thesis'},
                'source': 'http://base.uni-ak.ac.at/portfolio/taxonomy/master_thesis',
            }

        if author:
            entry.data['authors'] = [
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
            ]

        if language:
            entry.data['language'] = [
                {
                    'label': {
                        'de': 'Akan-Sprache',
                        'en': 'Akan',
                    },
                    'source': 'http://base.uni-ak.ac.at/portfolio/languages/ak',
                }
            ]

        entry.save()
        media = Media(
            owner=self.user,
            file=SimpleUploadedFile('example.txt', b'example text'),
            entry_id=entry.id,
        )
        if mime_type:
            media.mime_type = 'text/plain'
        if license_:
            media.license = {
                'label': {'en': 'Creative Commons Attribution 4.0'},
                'source': 'http://base.uni-ak.ac.at/portfolio/licenses/CC-BY-4.0',
            }

        media.save()
        return media


class ClientProvider:
    def __init__(self, model_provider: 'ModelProvider'):
        self.client = APIClient()
        r = self.client.login(username=model_provider.username, password=model_provider.peeword)
        if not r:
            raise RuntimeError('login fail')

    def get_media_primary_key_response(self, media: 'Media') -> 'Response':
        return self.client.get(
            f'/api/v1/validate_assets/media/{media.id}/',
        )

    def __del__(self):
        self.client.logout()  # Very important! ;-)
