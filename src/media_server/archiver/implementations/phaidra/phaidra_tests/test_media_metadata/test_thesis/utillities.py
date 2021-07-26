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
        respect_contributor_role: bool = True,
        respect_english_abstract_rule: bool = True,
        respect_german_abstract_rule: bool = True,
    ) -> dict:
        phaidra_container = deepcopy(cls.base)
        if respect_author_rule:
            phaidra_container['role:aut'].append(cls.author)
        if respect_language_rule:
            phaidra_container['dcterms:language'].append(cls.language)

        if respect_contributor_role:
            if 'role:supervisor' not in phaidra_container:
                phaidra_container['role:supervisor'] = []
            phaidra_container['role:supervisor'].append(cls.supervisor)

        if respect_english_abstract_rule:
            if 'bf:note' not in phaidra_container:
                phaidra_container['bf:note'] = []
            phaidra_container['bf:note'].append(cls.english_abstract)

        if respect_german_abstract_rule:
            if 'bf:note' not in phaidra_container:
                phaidra_container['bf:note'] = []
            phaidra_container['bf:note'].append(cls.german_abstract)

        return phaidra_container


class ModelProvider:
    def __init__(self):
        self.username = 'Φαίδρα'
        self.peeword = 'peeword'  # Yes, I am trying to trick some git hook …
        self.user = User.objects.create_user(username=self.username, password=self.peeword)

    def get_media(
        self,
        entry: 'Entry',
        license_: bool = True,
        mime_type: bool = True,
    ) -> 'Media':
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

    def get_entry(
        self,
        title: bool = True,
        type_: bool = True,
        author: bool = True,
        language: bool = True,
        advisor: bool = True,
        english_abstract: bool = True,
        german_abstract: bool = True,
        french_abstract: bool = False,
    ) -> 'Entry':
        """
        :param title: Mandatory field
        :param type_: Mandatory field
        :param author: Mandatory field
        :param language: Mandatory field
        :param advisor: Mandatory field
        :param english_abstract: Mandatory field
        :param german_abstract: Mandatory field
        :param french_abstract: Obligatory field
        :return:
        """
        entry = Entry(owner=self.user, data={})
        entry.update_archive = False
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

        if advisor:
            if 'contributors' not in entry.data:
                entry.data['contributors'] = []

            entry.data['contributors'].append(
                {
                    'label': 'Universität für Angewandte Kunst Wien',
                    'roles': [
                        {
                            'label': {'de': 'Betreuer', 'en': 'advisor'},
                            'source': 'http://base.uni-ak.ac.at/portfolio/vocabulary/advisor',
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

    def __del__(self):
        self.client.logout()  # Very important! ;-)
