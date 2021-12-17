import os
from datetime import datetime

import bibtexparser
from bibtexparser.bibdatabase import as_text
from marshmallow import ValidationError

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Entry
from core.schemas import TypeModelSchema
from core.schemas.entries.document import DocumentSchema
from core.schemas.general import (
    ContributorSchema,
    DateTimeSchema,
    LanguageDataSchema,
    MultilingualStringSchema,
    SourceMultilingualLabelSchema,
)
from core.schemas.models import KeywordsModelSchema, TextDataSchema, TextSchema
from portfolio import settings


class Command(BaseCommand):
    help = 'Creates new entries from entries in a BibTex file'

    def handle(self, *args, **options):

        # Open Bibtex-File
        with open(os.path.join(settings.BASE_DIR, 'migration/test.bib')) as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            published = False
            texts_all = None

            # Zuordnung Publikationsart -- entity.type
            if as_text(entry['ENTRYTYPE']) == 'article':
                entity_type = TypeModelSchema()
                sml = SourceMultilingualLabelSchema()
                ml = MultilingualStringSchema()
                ml.en = 'article'
                ml.de = 'Artikel'
                sml.source = 'http://base.uni-ak.ac.at/portfolio/taxonomy/article'
                sml.label = ml
                entity_type.type = sml
                # type_schema = TypeModelSchema()
                type_schema = SourceMultilingualLabelSchema()
                # entity_type_json = type_schema.dump(entity_type).data
                entity_type_json = type_schema.dump(sml).data
                # print("Typ: Dokument")

            if as_text(entry['ENTRYTYPE']) == 'inbook':
                entity_type = TypeModelSchema()
                sml = SourceMultilingualLabelSchema()
                ml = MultilingualStringSchema()
                ml.en = 'chapter'
                ml.de = 'Beitrag in Sammelband'
                sml.source = 'http://base.uni-ak.ac.at/portfolio/taxonomy/chapter'
                sml.label = ml
                entity_type.type = sml
                # type_schema = TypeModelSchema()
                type_schema = SourceMultilingualLabelSchema()
                # entity_type_json = type_schema.dump(entity_type).data
                entity_type_json = type_schema.dump(sml).data
                # print("Typ: Dokument")

            # Titel ######
            entity_title = as_text(entry['title'])
            print('Entity.Title = ', entity_title)

            # TEXT #######
            try:
                document_text_text = as_text(entry['abstract'])
                # print("document_text_text", document_text_text)
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
                print('Texte: ', texts_all)
            except KeyError:
                pass

            # ENTITY OWNER ######
            # Todo: Zuordnung zu User
            django_user, created = User.objects.get_or_create(username=1)

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
            # TODO FEHLERHAFT (REGEXP)
            try:
                date = DateTimeSchema()
                date_document = as_text(entry['year']) + '-' + as_text(entry['month']) + '-' + as_text(entry['day'])
                date.date = datetime.strptime(date_document, '%Y-%m-%d').date()
                print(date.date)
                document.date = date

            except KeyError:
                pass

            # LANGUAGE ###
            try:
                language = LanguageDataSchema()
                if as_text(entry['language']) == 'Deutsch':
                    language.source = 'http://base.uni-ak.ac.at/portfolio/languages/de'
                    mlstring1 = None
                    mlstring1 = MultilingualStringSchema()
                    mlstring1.de = 'Deutsch'
                    mlstring1.en = 'German'
                    mlstring1.fr = 'allemand'
                    language.label = mlstring1
                    document.language = language
                if as_text(entry['language']) == 'English':
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
                document.volume = as_text(entry['volume'])
            except KeyError:
                pass

            # PAGES ###
            try:
                document.pages = as_text(entry['pages'])
            except KeyError:
                pass

            # ISSN/ISBN ###
            try:
                document.isbn = as_text(entry['isbn'])
            except KeyError:
                pass
            try:
                document.isbn = as_text(entry['issn'])
            except KeyError:
                pass

            # DOI ###
            try:
                document.doi = as_text(entry['doi'])
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
                author.label = as_text(entry['author'])
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
                e_keywords.keywords = as_text(entry['keywords'])
            except KeyError:
                pass

            # CREATE ENTRY
            # CHECK SCHEMA COMPLIANCE
            try:
                schema.load(schema.dumps(document))
            except ValidationError as err:
                err.messages['_schema']
                print(err.messages)

            entity_data = schema.dump(document).data
            entity_keywords = keywordschema.dump(e_keywords).data

            # quick fix for invalid data
            texts_all = [texts_all] if texts_all else None
            if entity_keywords:
                entity_keywords = entity_keywords['keywords']

            publication = Entry.objects.create_clean(
                title=entity_title,
                type=entity_type_json,
                texts=texts_all,
                keywords=entity_keywords,
                owner_id=django_user.id,
                # owner_id=1,
                published=published,
                data=entity_data,
            )
            # owner_id=entity_owner)

            # publication.clean()
            # texts_all = None
            # e_keywords = []
            # keywordslist = []
            # published = False

            publication.save()
