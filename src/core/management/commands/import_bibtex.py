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
from core.schemas.general import ContributorSchema
from core.skosmos import get_preflabel


def get_label(uri, lang):
    return get_preflabel(uri.split('/')[-1], project=settings.TAX_ID, graph=settings.TAX_GRAPH, lang=lang)


def get_language_label(lang, label_lang):
    graph = 'http://base.uni-ak.ac.at/portfolio/languages/'
    return get_preflabel(lang, project=settings.LANGUAGES_VOCID, graph=graph, lang=label_lang)


def get_type_object(uri):
    return {
        'source': uri,
        'label': {
            'de': get_label(uri, 'de'),
            'en': get_label(uri, 'en'),
        },
    }


def get_text_object(text):
    return [
        {
            'text': text,
            'language': {
                'source': f'http://base.uni-ak.ac.at/portfolio/languages/{lang}',
            },
        }
        for lang in ['de', 'en']
    ]


def get_language_object(lang):
    return {
        'source': f'http://base.uni-ak.ac.at/portfolio/languages/{lang}',
        'label': {label_lang: get_language_label(lang, label_lang) for label_lang, _lstring in settings.LANGUAGES},
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
            texts = []

            # Type
            try:
                entry_type = type_mapping[bibtex_entry['ENTRYTYPE']]
            except KeyError:
                entry_type = None

            # Title
            if 'title' in bibtex_entry:
                entry_title = bibtex_entry['title']
            else:
                entry_title = 'no title'
                # TODO: add note that there was no title for this entry

            # Abstract
            if 'abstract' in bibtex_entry:
                texts.append(
                    {
                        'data': get_text_object(bibtex_entry['abstract']),
                        'type': get_type_object('http://base.uni-ak.ac.at/portfolio/vocabulary/abstract'),
                    }
                )

            # create DocumentSchema
            schema = DocumentSchema()
            document = DocumentSchema()

            # Date
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

            # Language
            if 'language' in bibtex_entry:
                # TODO: check if there is a good language string parser, so we can
                #       cater for all languages, we have in our vocabulary
                lang_string = bibtex_entry['language'].lower()
                if lang_string in ['de', 'deu', 'deutsch', 'german']:
                    document.language = get_language_object('de')
                elif lang_string in ['en', 'eng', 'english']:
                    document.language = get_language_object('en')

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

            notes_list = [f'Imported from {options["file"].name}']
            if entry_type is None:
                notes_list.append('\nNo matching type found for this entry. Collected data:')
                for key in bibtex_entry:
                    notes_list.append(f'{key}: {bibtex_entry[key]}')

            Entry.objects.create_clean(
                title=entry_title,
                type=entry_type,
                texts=texts,
                keywords=entry_keywords,
                owner_id=user.id,
                published=False,
                data=entry_data if entry_type else None,
                notes='\n'.join(notes_list),
            )
