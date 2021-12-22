import argparse
import re
from datetime import datetime

import bibtexparser
from marshmallow import ValidationError

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from core.models import Entry
from core.schemas import TypeModelSchema
from core.schemas.entries.document import DocumentSchema
from core.skosmos import get_preflabel


def get_label(uri, lang):
    return get_preflabel(uri.split('/')[-1], lang=lang)


def get_type_label(uri, lang):
    return get_preflabel(uri.split('/')[-1], project=settings.TAX_ID, graph=settings.TAX_GRAPH, lang=lang)


def get_language_label(lang, label_lang):
    graph = 'http://base.uni-ak.ac.at/portfolio/languages/'
    return get_preflabel(lang, project=settings.LANGUAGES_VOCID, graph=graph, lang=label_lang)


def get_role_object(uri):
    return {
        'source': uri,
        'label': {
            'de': get_label(uri, 'de'),
            'en': get_label(uri, 'en'),
        },
    }


def get_type_object(uri):
    return {
        'source': uri,
        'label': {
            'de': get_type_label(uri, 'de'),
            'en': get_type_label(uri, 'en'),
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
    record = month_to_numbers(record)
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


def month_to_numbers(record):
    month_map = {
        'January': '1',
        'February': '2',
        'March': '3',
        'April': '4',
        'May': '5',
        'June': '6',
        'July': '7',
        'August': '8',
        'September': '9',
        'October': '10',
        'November': '11',
        'December': '12',
    }
    if 'month' in record:
        if record['month'] in month_map:
            record['month'] = month_map[record['month']]
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
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        parser.customization = customizations
        try:
            bibtex_database = bibtexparser.load(options['file'], parser=parser)
        except Exception as err:
            raise CommandError(f'Error when loading BibTeX database: {repr(err)}')

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

        # list to track imported items
        imported = []

        for bibtex_entry in bibtex_database.entries:
            texts = []
            notes_list = [f'Imported from {options["file"].name}']
            location = []
            contributors = []
            published_in = {}

            # create DocumentSchema
            schema = DocumentSchema()
            document = DocumentSchema()

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
                notes_list.append('\nWarning: no title was set in this BibTeX entry')

            # Abstract
            if 'abstract' in bibtex_entry:
                texts.append(
                    {
                        'data': get_text_object(bibtex_entry['abstract']),
                        'type': get_type_object('http://base.uni-ak.ac.at/portfolio/vocabulary/abstract'),
                    }
                )

            # Address
            if 'address' in bibtex_entry:
                # TODO: should we also check for hits against PELIAS or just use the label?
                location.append({'label': bibtex_entry['address']})

            # Affiliation
            if 'affiliation' in bibtex_entry:
                contributors.append(
                    {
                        'label': bibtex_entry['affiliation'],
                        'roles': [get_role_object('http://base.uni-ak.ac.at/portfolio/vocabulary/organisation')],
                    }
                )

            # Annotation
            if 'annotation' in bibtex_entry:
                notes_list.append(f'\nAnnotation: {bibtex_entry["annotation"]}')

            # Authors
            if 'author' in bibtex_entry:
                authors = []
                for bibtex_author in bibtex_entry['author']:
                    author = {
                        'label': ' '.join(bibtex_author.split(', ')[::-1]),
                        'roles': [get_role_object('http://base.uni-ak.ac.at/portfolio/vocabulary/author')],
                    }
                    if author['label'] == user.get_full_name():
                        author['source'] = user.username
                    authors.append(author)
                document.authors = authors

            # Booktitle - The title of the book, if only part of it is being cited
            if 'booktitle' in bibtex_entry:
                published_in['title'] = bibtex_entry['booktitle']

            # Chapter
            # TODO: this seems not reasonably mappable, so putting it in notes
            #       but discuss if this is the way and update mapping document
            if 'chapter' in bibtex_entry:
                notes_list.append(f'\nUnmappable: chapter: {bibtex_entry["chapter"]}')

            # Contents
            if 'contents' in bibtex_entry:
                texts.append(
                    {
                        'data': get_text_object(bibtex_entry['contents']),
                        'type': get_type_object('http://base.uni-ak.ac.at/portfolio/vocabulary/description'),
                    }
                )

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

            # DOI
            if 'doi' in bibtex_entry:
                document.doi = bibtex_entry['doi']

            # Edition and Series
            edition = bibtex_entry.get('edition')
            series = bibtex_entry.get('series')
            if series and edition:
                # TODO: discuss how to format if both are set
                #       and shouldn't series in a monographic series rather be the published_in['title']
                document.edition = f'{series}. {edition}'
            elif series:
                document.edition = series
            elif edition:
                document.edition = edition

            # Editors
            if 'editor' in bibtex_entry:
                editors = []
                for bibtex_editor in bibtex_entry['editor']:
                    editor = {
                        'label': ' '.join(bibtex_editor['name'].split(', ')[::-1]),
                        'roles': [get_role_object('http://base.uni-ak.ac.at/portfolio/vocabulary/editor')],
                    }
                    if editor['label'] == user.get_full_name():
                        editor['source'] = user.username
                    editors.append(editor)
                document.editors = editors

            # Institution
            if 'institution' in bibtex_entry:
                contributors.append(
                    {
                        'label': bibtex_entry['institution'],
                        'roles': [
                            get_role_object('http://base.uni-ak.ac.at/portfolio/vocabulary/partner_institution')
                        ],
                    }
                )

            # ISSN/ISBN
            isbn = bibtex_entry.get('isbn')
            issn = bibtex_entry.get('issn')
            if isbn and issn:
                document.isbn = f'ISBN: {isbn} ISSN: {issn}'
            elif isbn:
                document.isbn = isbn
            elif issn:
                document.isbn = issn

            # Language
            if 'language' in bibtex_entry:
                # TODO: check if there is a good language string parser, so we can
                #       cater for all languages, we have in our vocabulary
                lang_string = bibtex_entry['language'].lower()
                if lang_string in ['de', 'deu', 'deutsch', 'german']:
                    document.language = get_language_object('de')
                elif lang_string in ['en', 'eng', 'english']:
                    document.language = get_language_object('en')

            # Journal
            # TODO: discuss how to handle cases where booktitle and journal are set
            #       currently journal will overwrite booktitle, but we could use
            #       the title/subtitle pair of published_in to store both
            if 'journal' in bibtex_entry:
                published_in['title'] = bibtex_entry['journal']

            # Location
            if 'location' in bibtex_entry:
                # TODO: should we also check for hits against PELIAS or just use the label?
                location.append({'label': bibtex_entry['location']})

            # Note
            if 'note' in bibtex_entry:
                notes_list.append(f'\nNote: {bibtex_entry["note"]}')

            # Number and volume
            volume = bibtex_entry.get('volume')
            number = bibtex_entry.get('number')
            if volume and number:
                document.volume = f'{volume} ({number})'
            elif volume:
                document.volume = volume
            elif number:
                document.volume = f'({number})'

            # Organization
            if 'organization' in bibtex_entry:
                contributors.append(
                    {
                        'label': bibtex_entry['organization'],
                        'roles': [get_role_object('http://base.uni-ak.ac.at/portfolio/vocabulary/organisation')],
                    }
                )

            # Pages
            if 'pages' in bibtex_entry:
                document.pages = bibtex_entry['pages']

            # Publisher
            if 'publisher' in bibtex_entry:
                document.publishers = [
                    {
                        'label': bibtex_entry['publisher'],
                        'roles': [get_role_object('http://base.uni-ak.ac.at/portfolio/vocabulary/publisher')],
                    }
                ]

            # School
            if 'school' in bibtex_entry:
                contributors.append(
                    {
                        'label': bibtex_entry['school'],
                        # TODO: this should become university/college when new vocabulary is deployed
                        'roles': [get_role_object('http://base.uni-ak.ac.at/portfolio/vocabulary/organisation')],
                    }
                )

            # Size
            if 'size' in bibtex_entry:
                # TODO: check first against formats in our vocabulary?
                document.format = [{'label': {lang: bibtex_entry['size'] for lang in ['de', 'en']}}]

            # URL
            if 'url' in bibtex_entry:
                document.url = bibtex_entry['url']

            # in case locations and contributors have been added, add them to document
            if location:
                document.location = location
            if contributors:
                document.contributors = contributors

            # if some published_in info was set, we add that too as a single item
            if published_in:
                document.published_in = [published_in]

            # CREATE ENTRY
            # CHECK SCHEMA COMPLIANCE
            try:
                schema.load(schema.dumps(document))
            except ValidationError as err:
                print(err.messages)

            entry_data = schema.dump(document).data

            entry_keywords = []
            if 'keywords' in bibtex_entry:
                # filter out duplicate keywords
                kw_labels = set()
                for kw in bibtex_entry.get('keywords'):
                    kw_labels.add(kw)
                # generate keyword labels with unique keywords
                for kw in kw_labels:
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

            imported.append((bibtex_entry['ID'], bibtex_entry['ENTRYTYPE']))

        # after all imports print success message with number of items
        # TODO: we could also display how many entries of each type.
        #       do we want to have that? maybe if a -v flag was set?
        self.stdout.write(self.style.SUCCESS(f'Successfuly imported {len(imported)} entries'))
