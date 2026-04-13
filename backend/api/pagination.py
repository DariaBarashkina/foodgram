from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class RecipePagination(PageNumberPagination):
    """
    Кастомная пагинация проекта Foodgram.

    Позволяет управлять количеством объектов через параметр `limit`.
    Возвращает ответ в формате, соответствующем документации:
    count, next, previous, results.
    """

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Формирует ответ с пагинацией в требуемом формате.
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
