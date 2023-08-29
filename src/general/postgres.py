from django.contrib.postgres.search import SearchVector
from django.db.models import FloatField, Func, JSONField, Value
from django.db.models.functions import Cast, Coalesce


class SearchVectorJSON(SearchVector):
    def __init__(self, *expressions, **extra):
        super().__init__(*expressions, **extra)
        self.source_expressions = [
            Coalesce(expression, Cast(Value('""'), JSONField()))
            for expression in self._parse_expressions(*expressions)
        ]


# Code from django 4.0


class TrigramWordBase(Func):
    output_field = FloatField()

    def __init__(self, string, expression, **extra):
        if not hasattr(string, 'resolve_expression'):
            string = Value(string)
        super().__init__(string, expression, **extra)


class TrigramWordSimilarity(TrigramWordBase):
    function = 'WORD_SIMILARITY'
