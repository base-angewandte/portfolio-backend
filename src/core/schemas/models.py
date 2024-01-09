from marshmallow import fields

from ..skosmos import get_preflabel_lazy
from .base import BaseSchema
from .general import LanguageDataSchema, SourceMultilingualLabelSchema

# schema definitions for entry model


# type
class TypeModelSchema(BaseSchema):
    type = fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False)


# keywords
class KeywordsModelSchema(BaseSchema):
    keywords = fields.List(
        fields.Nested(SourceMultilingualLabelSchema, additionalProperties=False)
    )


# texts
class TextDataSchema(BaseSchema):
    language = fields.Nested(LanguageDataSchema, additionalProperties=False)
    text = fields.Str(required=True, title=get_preflabel_lazy('text'))


class TextSchema(BaseSchema):
    type = fields.Nested(
        SourceMultilingualLabelSchema,
        additionalProperties=False,
        title=get_preflabel_lazy('type'),
    )
    data = fields.List(fields.Nested(TextDataSchema, additionalProperties=False))


class TextsModelSchema(BaseSchema):
    texts = fields.List(fields.Nested(TextSchema, additionalProperties=False))
