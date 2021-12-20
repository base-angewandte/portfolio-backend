import argparse
from datetime import datetime

import bibtexparser
from bibtexparser.bibdatabase import as_text
from marshmallow import ValidationError

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from core.models import Entry
from core.schemas import TypeModelSchema
from core.schemas.entries.document import DocumentSchema
from core.schemas.general import (
    ContributorSchema,
    LanguageDataSchema,
    MultilingualStringSchema,
    SourceMultilingualLabelSchema,
)
from core.schemas.models import KeywordsModelSchema, TextDataSchema, TextSchema
from core.skosmos import get_preflabel


def get_label(uri, lang):
    return get_preflabel(uri.split('/')[-1], project=settings.TAX_ID, graph=settings.TAX_GRAPH, lang=lang)


def get_type_object(uri):
    return {
        'source': uri,
        'label': {
            'de': get_label(uri, 'de'),
            'en': get_label(uri, 'en'),
        },
    }


class Command(BaseCommand):
    help = 'Creates new entries from entries in a BibTeX file'

    def add_arguments(self, parser):
        parser.add_argument('user', type=str, help='Username of the user to import entries for')
        parser.add_argument('file', type=argparse.FileType('r'), help='BibTeX file to import from')

    def handle(self, *args, **options):

        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError('User does not exist')

        # Parse BibTeX-File
        bibtex_database = bibtexparser.load(options['file'])

        # type mapping
        # bibtex type as keys
        # type object as values
        type_mapping = {
            'article': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/article'),
            'inbook': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/chapter'),
        }

        # ensure type objects are still valid
        for _k, v in type_mapping.items():
            TypeModelSchema().load({'type': v})

        for bibtex_entry in bibtex_database.entries:
            texts_all = None

            # Type
            entry_type = type_mapping[as_text(bibtex_entry['ENTRYTYPE'])]

            # Title
            entry_title = as_text(bibtex_entry['title'])

            # TEXT #######
            try:
                document_text_text = as_text(bibtex_entry['abstract'])
                text_allg = TextSchema()
                texts = TextSchema()
                text_allg_type = SourceMultilingualLabelSchema()
                text_allg_type.source = 'http://base.uni-ak.ac.at/portfolio/vocabulary/abstract'
                mlstring1 = None
                mlstring1 = MultilingualStringSchema()
                mlstring1.de = 'Abstract'
                mlstring1.en = 'abstract'
                text_allg_type.label = mlstring1
                text_data_allg = TextDataSchema()
                text_data_allg_language = LanguageDataSchema()
                text_data_allg_language.source = 'http://base.uni-ak.ac.at/portfolio/languages/de'
                mlstring1 = None
                mlstring1 = MultilingualStringSchema()
                mlstring1.de = 'Deutsch'
                mlstring1.en = 'German'
                mlstring1.fr = 'allemand'
                text_data_allg_language.label = mlstring1
                text_data_allg.text = document_text_text
                text_data_allg.language = text_data_allg_language
                text_allg.data = text_data_allg
                text_allg.type = text_allg_type
                texts_all = texts.dump(text_allg).data
            except KeyError:
                pass

            # create PublishedInSchema
            # Todo: Wird das Schema benötigt?
            # SCHEMA #####
            # schema = PublishedInSchema()
            # publishedIn = PublishedInSchema()
            # # title = get_string_field(get_preflabel_lazy('title'), {'field_format': 'half', 'order': 1})
            # # subtitle = get_string_field(get_preflabel_lazy('subtitle'), {'field_format': 'half', 'order': 2})
            # # editor = get_contributors_field_for_role('editor', {'order': 3})
            # # publisher = get_contributors_field_for_role('publisher', {'order': 4})
            # title =
            # subtitle =
            # editor = None
            # editor = ContributorSchema()
            # editor.label = personname['firstname'] + " " + personname['secondname']
            # editor.source = entity_owner_uuid
            # role = None
            # role = SourceMultilingualLabelSchema()
            # mlstring1 = None
            # mlstring1 = MultilingualStringSchema()
            # mlstring1.de = "Künstler*in"
            # mlstring1.en = "artist"
            # role.label = mlstring1
            # role.source = "http://base.uni-ak.ac.at/portfolio/vocabulary/artist"
            # roles.append(role)
            # artist1.source = entity_owner_uuid
            # editor.roles = role
            # publishedIn.editor = editor

            # Publisher ####
            # Todo: Wird das Schema benötigt?
            # publisher = None
            # publisher = ContributorSchema()
            # publisher.label = personname['firstname'] + " " + personname['secondname']
            # publisher.source = entity_owner_uuid
            # role = None
            # role = SourceMultilingualLabelSchema()
            # mlstring1 = None
            # mlstring1 = MultilingualStringSchema()
            # mlstring1.de = "Künstler*in"
            # mlstring1.en = "artist"
            # role.label = mlstring1
            # role.source = "http://base.uni-ak.ac.at/portfolio/vocabulary/artist"
            # roles.append(role)
            # artist1.source = entity_owner_uuid
            # publisher.roles = role
            # publishedIn.publisher = publisher

            # KEYWORDS ###
            keywordschema = KeywordsModelSchema()
            e_keywords = KeywordsModelSchema()

            # create DocumentSchema
            schema = DocumentSchema()
            document = DocumentSchema()

            # DATE ###
            # TODO: review: how do we want to handle dates where only year or year and month are set?
            year = bibtex_entry.get('year')
            month = bibtex_entry.get('month')
            day = bibtex_entry.get('day')
            if year is not None:
                date_string = year
                date_format = '%Y'
                if month:
                    date_string += f'-{month}'
                    date_format += '-%m'
                    if day:
                        date_string += f'-{day}'
                        date_format += '-%d'
                document.date = datetime.strptime(date_string, date_format).date()

            # LANGUAGE ###
            try:
                language = LanguageDataSchema()
                if as_text(bibtex_entry['language']) == 'Deutsch':
                    language.source = 'http://base.uni-ak.ac.at/portfolio/languages/de'
                    mlstring1 = None
                    mlstring1 = MultilingualStringSchema()
                    mlstring1.de = 'Deutsch'
                    mlstring1.en = 'German'
                    mlstring1.fr = 'allemand'
                    language.label = mlstring1
                    document.language = language
                if as_text(bibtex_entry['language']) == 'English':
                    language.source = 'http://base.uni-ak.ac.at/portfolio/languages/en'
                    mlstring1 = None
                    mlstring1 = MultilingualStringSchema()
                    mlstring1.de = 'Englisch'
                    mlstring1.en = 'English'
                    mlstring1.fr = 'anglais'
                    language.label = mlstring1
                    document.language = language
            except KeyError:
                pass

            # VOLUME ###
            try:
                document.volume = as_text(bibtex_entry['volume'])
            except KeyError:
                pass

            # PAGES ###
            try:
                document.pages = as_text(bibtex_entry['pages'])
            except KeyError:
                pass

            # ISSN/ISBN ###
            try:
                document.isbn = as_text(bibtex_entry['isbn'])
            except KeyError:
                pass
            try:
                document.isbn = as_text(bibtex_entry['issn'])
            except KeyError:
                pass

            # DOI ###
            try:
                document.doi = as_text(bibtex_entry['doi'])
            except KeyError:
                pass

            # ÜBERBLICK DOCUMENTSCHEMA
            # authors = get_contributors_field_for_role('author', {'order': 1})
            # editors = get_contributors_field_for_role('editor', {'order': 2})
            # publishers = get_contributors_field_for_role('publisher', {'order': 3})
            # date = get_date_field({'order': 4})
            # location = get_location_field({'order': 5})
            # isbn/issn
            # isbn = get_string_field(get_preflabel_lazy('isbn'), {'field_format': 'half', 'order': 6})
            # doi = get_string_field(get_preflabel_lazy('doi'), {'field_format': 'half', 'order': 7})
            # url = get_url_field({'order': 8})
            # published_in = fields.List(
            #     fields.Nested(PublishedInSchema, additionalProperties=False),
            #     title=get_preflabel_lazy('published_in'),
            #     **{'x-attrs': {'field_type': 'group', 'show_label': True, 'order': 9}},
            # )
            # volume = get_string_field(get_preflabel_lazy('volume_issue'), {'field_format': 'half', 'order': 10})
            # pages = get_string_field(get_preflabel_lazy('pages'), {'field_format': 'half', 'order': 11})
            # contributors = get_contributors_field({'order': 12})
            # language = get_language_list_field({'order': 13})
            # material = get_material_field({'order': 14, 'field_format': 'half'})
            # format = get_format_field({'order': 15})
            # edition = get_string_field(get_preflabel_lazy('edition'), {'field_format': 'half', 'order': 16})

            # AUTHOR ###
            authors = []
            author = None
            author = ContributorSchema()
            try:
                author.label = as_text(bibtex_entry['author'])
                roles = []
                role = None
                role = SourceMultilingualLabelSchema()
                mlstring1 = None
                mlstring1 = MultilingualStringSchema()
                mlstring1.de = 'Author*in'
                mlstring1.en = 'author'
                role.label = mlstring1
                role.source = 'http://base.uni-ak.ac.at/portfolio/vocabulary/author'
                roles.append(role)
                author.roles = role
                authors.append(author)
            except KeyError:
                pass
            document.authors = authors

            # Editor ####
            # Todo: Wird das Schema benötigt?
            # editors = []
            # editor = None
            # editor = ContributorSchema()
            # editor.label = personname['firstname'] + " " + personname['secondname']
            # editor.source = entity_owner_uuid
            # role = None
            # role = SourceMultilingualLabelSchema()
            # mlstring1 = None
            # mlstring1 = MultilingualStringSchema()
            # mlstring1.de = "Künstler*in"
            # mlstring1.en = "artist"
            # role.label = mlstring1
            # role.source = "http://base.uni-ak.ac.at/portfolio/vocabulary/artist"
            # roles.append(role)
            # artist1.source = entity_owner_uuid
            # editor.roles = role
            # editors.append(editor)

            keywordschema = KeywordsModelSchema()
            e_keywords = KeywordsModelSchema()
            try:
                e_keywords.keywords = as_text(bibtex_entry['keywords'])
            except KeyError:
                pass

            # CREATE ENTRY
            # CHECK SCHEMA COMPLIANCE
            try:
                schema.load(schema.dumps(document))
            except ValidationError as err:
                err.messages['_schema']
                print(err.messages)

            entry_data = schema.dump(document).data
            entry_keywords = keywordschema.dump(e_keywords).data

            # quick fix for invalid data
            texts_all = [texts_all] if texts_all else None
            if entry_keywords:
                entry_keywords = entry_keywords['keywords']

            publication = Entry.objects.create_clean(
                title=entry_title,
                type=entry_type,
                texts=texts_all,
                keywords=entry_keywords,
                owner_id=user.id,
                # owner_id=1,
                published=False,
                data=entry_data,
            )
            # owner_id=entity_owner)

            # publication.clean()
            # texts_all = None
            # e_keywords = []
            # keywordslist = []
            # published = False

            publication.save()
