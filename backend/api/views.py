from django.db.models import F, Sum
from django.http import FileResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipePagination
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """Вьюсет пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = RecipePagination

    @action(
        detail=False, methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': pk},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        deleted, _ = Subscription.objects.filter(
            user=request.user, author_id=pk
        ).delete()
        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
                if deleted
                else status.HTTP_400_BAD_REQUEST
            )
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            followers__user=request.user
        ).annotate(recipes_count=Sum('recipes__id'))

        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Теги."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ингредиенты."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты."""

    queryset = Recipe.objects.all()
    pagination_class = RecipePagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_to(self, model, user, recipe):
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'detail': 'Уже добавлено'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    def _delete_from(self, model, user, recipe):
        deleted, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
                if deleted
                else status.HTTP_400_BAD_REQUEST
            )
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self._add_to(Favorite, request.user, self.get_object())

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._delete_from(Favorite, request.user, self.get_object())

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self._add_to(ShoppingCart, request.user, self.get_object())

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._delete_from(ShoppingCart, request.user, self.get_object())

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        url = reverse('recipe-short-link', args=[pk])
        return Response({'short-link': request.build_absolute_uri(url)})

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit'),
        ).annotate(total=Sum('amount')).order_by('name')

        content = '\n'.join(
            f"{item['name']} ({item['unit']}) — {item['total']}"
            for item in ingredients
        )

        response = FileResponse(
            content.encode(),
            content_type='text/plain'
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response
