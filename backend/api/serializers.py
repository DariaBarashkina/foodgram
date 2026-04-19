from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.constants import (
    MAX_COOKING_TIME,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
    MAX_INGREDIENT_AMOUNT,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = tuple(DjoserUserSerializer.Meta.fields) + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.subscriptions_to_author.filter(user=request.user).exists()
        )

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else None


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        return {'avatar': instance.avatar.url if instance.avatar else None}


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        return obj.image.url if obj.image else None


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='ingredient_in_recipe',
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
            'pub_date',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.shopping_cart.filter(user=request.user).exists()
        )

    def get_image(self, obj):
        return obj.image.url if obj.image else None


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT,
    )


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
    )
    image = Base64ImageField()
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        )
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле'}
            )

        ingredient_ids = [item['id'].pk for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться'}
            )

        if not tags:
            raise serializers.ValidationError({'tags': 'Обязательное поле'})

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться'}
            )

        return data

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    @staticmethod
    def bulk_create_ingredients(recipe, ingredients):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            )
            for item in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.bulk_create_ingredients(recipe, ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        if tags:
            instance.tags.set(tags)

        if ingredients:
            instance.ingredient_in_recipe.all().delete()
            self.bulk_create_ingredients(instance, ingredients)

        return super().update(instance, validated_data)


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(UserSerializer.Meta):
        fields = tuple(UserSerializer.Meta.fields) + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()

        if request:
            limit = request.query_params.get('recipes_limit')
            try:
                limit = int(limit)
                if limit > 0:
                    recipes = recipes[:limit]
            except (TypeError, ValueError):
                pass

        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']

        if user == author:
            raise serializers.ValidationError(
                {'author': 'Нельзя подписаться на себя'}
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'author': 'Вы уже подписаны'}
            )

        return attrs

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.author,
            context=self.context
        ).data


class RecipeRelationSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, attrs):
        model = self.Meta.model
        user = attrs['user']
        recipe = attrs['recipe']

        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {
                    'recipe': f'{model._meta.verbose_name} уже существует'
                }
            )

        return attrs

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(RecipeRelationSerializer):
    class Meta(RecipeRelationSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(RecipeRelationSerializer):
    class Meta(RecipeRelationSerializer.Meta):
        model = ShoppingCart
