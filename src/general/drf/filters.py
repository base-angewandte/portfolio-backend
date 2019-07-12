from rest_framework.filters import OrderingFilter

from django.db.models.functions import Lower


# from https://github.com/encode/django-rest-framework/issues/3280
class CaseInsensitiveOrderingFilter(OrderingFilter):

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            new_ordering = []
            for field in ordering:
                if any(x in field for x in ['date', 'published']):
                    new_ordering.append(field)
                elif field.startswith('-'):
                    new_ordering.append(Lower(field[1:]).desc())
                else:
                    new_ordering.append(Lower(field).asc())
            return queryset.order_by(*new_ordering)

        return queryset
