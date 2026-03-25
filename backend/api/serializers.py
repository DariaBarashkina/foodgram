import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для декодирования base64 изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return obj.avatar.url
        return None


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для подписок с рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit and limit.isdigit():
            recipes = recipes[: int(limit)]
        serializer = ShortRecipeSerializer(
            recipes, many=True, context={'request': request}
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='ingredient_in_recipe'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return obj.image.url
        return None


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецептов."""

    ingredients = IngredientInRecipeCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно указать хотя бы один ингредиент'
            )
        ingredients = [item['id'] for item in value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Нужно указать хотя бы один тег')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться')
        return value

    def create_ingredients(self, ingredients, recipe):
        ingredient_objects = []
        for ingredient_data in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data['id']
            )
            ingredient_objects.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount'],
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredient_objects)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.ingredient_in_recipe.all().delete()
            self.create_ingredients(ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = RecipeSerializer(instance, context={'request': request})
        return serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для рецептов."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return obj.image.url
        return None


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = ShortRecipeSerializer(
            instance.recipe, context={'request': request}
        )
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = ShortRecipeSerializer(
            instance.recipe, context={'request': request}
        )
        return serializer.data
