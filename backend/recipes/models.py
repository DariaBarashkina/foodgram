import random
import string

from django.core.validators import MinValueValidator
from django.db import models

from recipes.constants import (
    MAX_INGREDIENT_NAME_LENGTH,
    MAX_MEASUREMENT_UNIT_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_SLUG_LENGTH,
    MAX_TAG_NAME_LENGTH,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
)
from users.models import User


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        'Название',
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=MAX_SLUG_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        'Название',
        max_length=MAX_INGREDIENT_NAME_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_MEASUREMENT_UNIT_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название',
        max_length=MAX_RECIPE_NAME_LENGTH
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/'
    )
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=(MinValueValidator(MIN_COOKING_TIME),)
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    short_code = models.CharField(max_length=10, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = ''.join(
                random.choices(string.ascii_letters + string.digits, k=6)
            )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Промежуточная модель ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(MinValueValidator(MIN_INGREDIENT_AMOUNT),)
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            ),
        )

    def __str__(self):
        return f'{self.ingredient.name} - {self.amount}'


class Favorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            ),
        )

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            ),
        )

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name}'
