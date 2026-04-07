from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
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
from .pagination import CustomPagination
from .serializers import (
    AvatarSerializer,
    CustomUserCreateSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Разрешение: редактировать может только автор."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in ('GET', 'HEAD', 'OPTIONS')
            or obj.author == request.user
        )


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователей."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'create':
            return (AllowAny(),)
        return (IsAuthenticatedOrReadOnly(),)

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        """Текущий пользователь."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Добавление/удаление аватара."""
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        """Подписка/отписка."""
        author = get_object_or_404(User, pk=pk)

        if request.user == author:
            raise ValidationError('Нельзя подписаться на себя')

        if request.method == 'POST':
            if Subscription.objects.filter(
                user=request.user, author=author
            ).exists():
                raise ValidationError('Вы уже подписаны')

            Subscription.objects.create(
                user=request.user, author=author
            )

            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()

        if not deleted:
            raise ValidationError('Вы не были подписаны')

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Список подписок."""
        authors = User.objects.filter(following__user=request.user)

        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Теги."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ингредиенты."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт из избранного."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                raise ValidationError('Рецепт уже в избранном')

            Favorite.objects.create(user=user, recipe=recipe)

            serializer = ShortRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Favorite.objects.filter(
            user=user, recipe=recipe
        ).delete()

        if not deleted:
            raise ValidationError('Рецепта нет в избранном')

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт из списка покупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists():
                raise ValidationError('Рецепт уже в списке покупок')

            ShoppingCart.objects.create(user=user, recipe=recipe)

            serializer = ShortRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()

        if not deleted:
            raise ValidationError('Рецепта нет в списке покупок')

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/s/{recipe.id}/')
        return Response({'short-link': link})

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        ingredients = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_cart__user=request.user
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(total=Sum('amount'))
        )

        content = 'Список покупок:\n'
        for item in ingredients:
            content += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total']}\n"
            )

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


def index(request):
    """Заглушка для главной страницы."""
    return render(request, 'index.html')
