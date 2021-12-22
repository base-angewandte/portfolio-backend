import argparse
import re
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
from core.schemas.models import TextDataSchema, TextSchema
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


def customizations(record):
    """Wrapper for all bibtexparser customizations used in this importer."""
    record = bibtexparser.customization.convert_to_unicode(record)
    record = bibtexparser.customization.author(record)
    record = bibtexparser.customization.editor(record)
    record = bibtexparser.customization.keyword(record)
    record = keywords(record)
    return record


def keywords(record, sep=',|;'):
    """Split keywords field into a list.

    For some reason the bibtexparser.customization only contains a keyword function,
    operating on a 'keyword' key in the record. So we add the same code here for
    a 'keywords' key.

    :param record: the record.
    :type record: dict
    :param sep: pattern used for the splitting regexp.
    :type record: string, optional
    :returns: dict -- the modified record.
    """
    if 'keywords' in record:
        record['keywords'] = [i.strip() for i in re.split(sep, record['keywords'].replace('\n', ''))]

    return record


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
        parser = bibtexparser.bparser.BibTexParser()
        parser.customization = customizations
        bibtex_database = bibtexparser.load(options['file'], parser=parser)

        # type mapping
        # bibtex type as keys
        # type object as values
        type_mapping = {
            'article': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/article'),
            'book': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/scientific_publication'),
            'booklet': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/catalogue'),
            'conference': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/catalogue'),
            'inproceedings': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/conference_proceedings'),
            'inbook': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/chapter'),
            'incollection': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/series_monographic_series'),
            'manual': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/scientific_publication'),
            'masterthesis': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/master_thesis'),
            'phdthesis': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/doctoral_dissertation'),
            'proceedings': get_type_object('http://base.uni-ak.ac.at/portfolio/taxonomy/conference_proceedings'),
        }

        # ensure type objects are still valid
        for _k, v in type_mapping.items():
            TypeModelSchema().load({'type': v})

        for bibtex_entry in bibtex_database.entries:
            texts_all = None

            # Type
            try:
                entry_type = type_mapping[bibtex_entry['ENTRYTYPE']]
            except KeyError:
                entry_type = None

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
            if 'author' in bibtex_entry:
                for bibtex_author in bibtex_entry['author']:
                    author = ContributorSchema()
                    author.label = ' '.join(bibtex_author.split(', ')[::-1])
                    if author.label == user.get_full_name():
                        author.source = user.username
                    author_concept = 'http://base.uni-ak.ac.at/portfolio/vocabulary/author'
                    author.roles = [
                        {
                            'source': author_concept,
                            'label': {
                                'de': get_label(author_concept, 'de'),
                                'en': get_label(author_concept, 'en'),
                            },
                        }
                    ]
                    authors.append(author)
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

            # CREATE ENTRY
            # CHECK SCHEMA COMPLIANCE
            try:
                schema.load(schema.dumps(document))
            except ValidationError as err:
                err.messages['_schema']
                print(err.messages)

            entry_data = schema.dump(document).data

            entry_keywords = []
            if 'keywords' in bibtex_entry:
                for kw in bibtex_entry.get('keywords'):
                    # TODO: here we could check first if a keyword in out taxonomy already
                    #       exists, and then use this concept and its translations
                    entry_keywords.append(
                        {
                            'label': {
                                'de': kw,
                                'en': kw,
                            },
                        }
                    )

            # quick fix for invalid data
            texts_all = [texts_all] if texts_all else None

            notes_list = [f'Imported from {options["file"].name}']
            if entry_type is None:
                notes_list.append('\nNo matching type found for this entry. Collected data:')
                for key in bibtex_entry:
                    notes_list.append(f'{key}: {bibtex_entry[key]}')

            Entry.objects.create_clean(
                title=entry_title,
                type=entry_type,
                texts=texts_all,
                keywords=entry_keywords,
                owner_id=user.id,
                published=False,
                data=entry_data if entry_type else None,
                notes='\n'.join(notes_list),
            )
