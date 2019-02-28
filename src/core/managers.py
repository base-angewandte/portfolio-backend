from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db import models

from general.postgres import SearchVectorJSON

search_vectors = (
    SearchVector('title', weight='A') +
    SearchVector('subtitle', weight='B') +
    SearchVectorJSON('texts', weight='B') +
    SearchVectorJSON('data', weight='B') +
    SearchVector('notes', weight='C')
)


class EntityManager(models.Manager):
    def search(self, text):
        search_query = SearchQuery(text)
        search_rank = SearchRank(search_vectors, search_query) + TrigramSimilarity('title', text)
        return self.get_queryset().annotate(rank=search_rank).filter(rank__gte=0.3).order_by('-rank')
