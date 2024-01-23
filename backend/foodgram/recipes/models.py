from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    slug = models.SlugField(
        blank=True,
        verbose_name='Слаг'
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        verbose_name='Цвет'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug[:settings.FIELD_SLICE]


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name[:settings.FIELD_SLICE]


class Recipe(models.Model):
    """Модель рецептов."""
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    image = models.ImageField(
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(1)
        ]
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:settings.FIELD_SLICE]


class RecipeTag(models.Model):
    """Модель связей рецептов и тегов."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        verbose_name = 'Теги рецепта'
        verbose_name_plural = 'Теги рецептов'

    def __str__(self):
        return (
            f'{self.recipe.name[:settings.FIELD_SLICE]} - '
            f'{self.tag.slug[:settings.FIELD_SLICE]}'
        )


class RecipeIngredient(models.Model):
    """Модель связей рецептов и ингредиентов."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='amount_ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return (
            f'{self.recipe.name[:settings.FIELD_SLICE]} - '
            f'{self.ingredient.name[:settings.FIELD_SLICE]}'
        )


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping',
        verbose_name='Владелец'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'recipe'], name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return (
            f'{self.recipe.name[:settings.FIELD_SLICE]} - '
            f'{self.owner.username[:settings.FIELD_SLICE]}'
        )


class Favorite(models.Model):
    """Модель избранного."""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorited',
        verbose_name='Владелец'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorited'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'recipe'], name='unique_favorite'
            )
        ]

    def __str__(self):
        return (
            f'{self.recipe.name[:settings.FIELD_SLICE]} - '
            f'{self.owner.username[:settings.FIELD_SLICE]}'
        )
