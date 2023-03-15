import re as regex

from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy

from core.skosmos import get_preflabel_languages_lazy, get_preflabel_lazy

single_field_template = gettext_lazy('Field "{field}" is required.')
# This is for testing. That is suboptimal here, but it is clearest solution, I have in mind right now.
missing_field_message_pattern = regex.compile(r'Field "\w+" is required.')

# https://voc.uni-ak.ac.at/skosmos/povoc/en/page/author
MISSING_AUTHOR = format_lazy(single_field_template, field=get_preflabel_lazy('author'))
# https://voc.uni-ak.ac.at/skosmos/povoc/en/page/supervisor
MISSING_SUPERVISOR = format_lazy(single_field_template, field=get_preflabel_lazy('supervisor'))
# https://voc.uni-ak.ac.at/skosmos/povoc/en/page/language
MISSING_LANGUAGE = format_lazy(single_field_template, field=get_preflabel_lazy('language'))

missing_text_in_language_template = 'A/an "{abstract}" in "{language}" is required.'
# This is for testing. That is suboptimal here, but it is clearest solution, I have in mind right now.
missing_text_in_language_message_pattern = regex.compile(r'A/an "\w+" in "\w+" is required.')

# https://voc.uni-ak.ac.at/skosmos/povoc/de/page/abstract
# https://voc.uni-ak.ac.at/skosmos/languages/de/page/en
MISSING_ENGLISH_ABSTRACT = format_lazy(
    missing_text_in_language_template,
    abstract=get_preflabel_lazy('abstract'),
    language=get_preflabel_languages_lazy('en'),
)

# https://voc.uni-ak.ac.at/skosmos/povoc/de/page/abstract
# https://voc.uni-ak.ac.at/skosmos/languages/de/page/de
MISSING_GERMAN_ABSTRACT = format_lazy(
    missing_text_in_language_template,
    abstract=get_preflabel_lazy('abstract'),
    language=get_preflabel_languages_lazy('de'),
)
