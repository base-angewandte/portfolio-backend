from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models

from general.postgres import SearchVectorJSON, TrigramWordSimilarity

search_vectors = (
    SearchVector('title', weight='A')
    + SearchVector('subtitle', weight='B')
    + SearchVectorJSON('texts', weight='B')
    + SearchVectorJSON('data', weight='B')
    + SearchVectorJSON('keywords', weight='B')
    + SearchVector('notes', weight='C')
)


class EntryManager(models.Manager):
    def create_clean(self, **kwargs):
        entry = self.model(**kwargs)
        entry.full_clean()
        entry.save()
        return entry

    def search(self, text):
        search_query = SearchQuery(text)
        search_rank = SearchRank(search_vectors, search_query)
        trigram_word_similarity_title = TrigramWordSimilarity(text, 'title')
        rank = search_rank + trigram_word_similarity_title
        return (
            self.get_queryset()
            .annotate(rank=rank)
            .filter(rank__gte=0.2)
            .order_by('-rank')
        )
