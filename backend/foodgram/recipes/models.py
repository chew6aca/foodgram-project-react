from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from core import constants

User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(
        max_length=constants.TAG_NAME_LEN,
        verbose_name='Название'
    )
    slug = models.SlugField(
        blank=True,
        verbose_name='Слаг',
        max_length=constants.TAG_SLUG_LEN
    )
    color = ColorField(
        blank=True,
        verbose_name='Цвет')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug[:constants.SLICE_LEN]


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        max_length=constants.INGREDIENT_NAME_LEN,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=constants.MEASUREMENT_LEN,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_ingredient'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name[:constants.SLICE_LEN]


class Recipe(models.Model):
    """Модель рецептов."""
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги'
    )
    name = models.CharField(
        max_length=constants.RECIPE_NAME,
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
            MinValueValidator(
                constants.COOKING_TIME_MIN,
                message=(
                    'Время готовки не может быть меньше '
                    f'{constants.COOKING_TIME_MIN} мин.'
                )
            ),
            MaxValueValidator(
                constants.COOKING_TIME_MAX,
                message=(
                    f'Нельзя готовить дольше {constants.COOKING_TIME_MAX} мин.'
                )
            )
        ]
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:constants.SLICE_LEN]


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
        return (f'Тег рецепта {self.id}')


class RecipeIngredient(models.Model):
    """Модель связей рецептов и ингредиентов."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='amount_ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='amount_ingredient'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return (f'Ингредиент рецепта {self.id}')


class OwnerRecipeBaseModel(models.Model):
    """Базовая модель."""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'recipe'], name='%(class)s_unique'
            )
        ]


class ShoppingCart(OwnerRecipeBaseModel):
    """Модель списка покупок."""

    class Meta(OwnerRecipeBaseModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping'

    def __str__(self):
        return (f'Рецепт в списке покупок {self.id}')


class Favorite(OwnerRecipeBaseModel):
    """Модель избранного."""

    class Meta(OwnerRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorited'

    def __str__(self):
        return (f'Рецепт в избранном {self.id}')
