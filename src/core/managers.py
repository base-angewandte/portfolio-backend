from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db import models

from general.postgres import SearchVectorJSON

search_vectors = (
    SearchVector('title', weight='A')
    + SearchVector('subtitle', weight='B')
    + SearchVectorJSON('texts', weight='B')
    + SearchVectorJSON('data', weight='B')
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
        trigram_similarity_title = TrigramSimilarity('title', text)
        rank = search_rank + trigram_similarity_title
        return self.get_queryset().annotate(rank=rank).filter(rank__gte=0.2).order_by('-rank')
