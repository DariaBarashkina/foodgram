from django_filters import rest_framework as filters

from recipes.constants import TRUE_VALUE
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """Фильтр для поиска ингредиентов по названию."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр рецептов."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags',)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user

        if not value or not user.is_authenticated:
            return queryset

        if int(value) == TRUE_VALUE:
            return queryset.filter(favorites__user=user).distinct()

        return queryset.exclude(favorites__user=user).distinct()

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user

        if not value or not user.is_authenticated:
            return queryset

        if int(value) == TRUE_VALUE:
            return queryset.filter(shopping_cart__user=user).distinct()

        return queryset.exclude(shopping_cart__user=user).distinct()
