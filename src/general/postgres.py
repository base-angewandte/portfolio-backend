from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVector
from django.db.models.expressions import Value
from django.db.models.functions import Cast, Coalesce


class SearchVectorJSON(SearchVector):
    def __init__(self, *expressions, **extra):
        super(SearchVectorJSON, self).__init__(*expressions, **extra)
        self.source_expressions = [
            Coalesce(expression, Cast(Value('""'), JSONField())) for expression in self._parse_expressions(*expressions)
        ]
