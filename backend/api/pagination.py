from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """
    Пагинация проекта Foodgram.

    Позволяет управлять количеством объектов через параметр `limit`.
    """

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100
