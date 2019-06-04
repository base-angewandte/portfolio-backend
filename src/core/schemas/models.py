from marshmallow import Schema, fields

from .general import SourceMultilingualLabelSchema, LanguageDataSchema
from ..skosmos import get_preflabel_lazy


# schema definitions for entry model

# keywords
class KeywordsModelSchema(Schema):
    keywords = fields.List(fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False))


# texts
class TextDataSchema(Schema):
    language = fields.Nested(LanguageDataSchema, additionalProperties=False)
    text = fields.Str(required=True, title=get_preflabel_lazy('text'))


class TextSchema(Schema):
    type = fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False, title=get_preflabel_lazy('type'))
    data = fields.List(fields.Nested(TextDataSchema, additionalProperties=False))


class TextsModelSchema(Schema):
    texts = fields.List(fields.Nested(TextSchema, additionalProperties=False))
