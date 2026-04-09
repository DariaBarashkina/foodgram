from django_filters import rest_framework as filters

from recipes.constants import FALSE_VALUE, TRUE_VALUE
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """
    Фильтр для поиска ингредиентов по названию.

    Поиск выполняется по началу строки (без учета регистра).
    """

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """
    Фильтр рецептов.

    Поддерживает:
    - фильтрацию по автору
    - фильтрацию по тегам (slug)
    - фильтрацию по избранному (0/1)
    - фильтрацию по списку покупок (0/1)
    """

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    author = filters.NumberFilter()

    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация по избранному.

        TRUE_VALUE (1) → только избранные
        FALSE_VALUE (0) → исключить избранные
        """
        user = self.request.user

        if value == TRUE_VALUE:
            if not user.is_authenticated:
                return queryset.none()
            return queryset.filter(
                favorites__user=user
            ).distinct()

        if value == FALSE_VALUE and user.is_authenticated:
            return queryset.exclude(
                favorites__user=user
            ).distinct()

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация по списку покупок.

        TRUE_VALUE (1) → только в списке покупок
        FALSE_VALUE (0) → исключить
        """
        user = self.request.user

        if value == TRUE_VALUE:
            if not user.is_authenticated:
                return queryset.none()
            return queryset.filter(
                shopping_cart__user=user
            ).distinct()

        if value == FALSE_VALUE and user.is_authenticated:
            return queryset.exclude(
                shopping_cart__user=user
            ).distinct()

        return queryset
