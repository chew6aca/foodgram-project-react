from django_filters import FilterSet
from django_filters.filters import CharFilter, ModelMultipleChoiceFilter

from recipes.models import Ingredient, Recipe, Tag


class RecipeModelFilter(FilterSet):
    """Фильтерсет рецептов."""
    is_favorited = CharFilter(method='is_favorited_filter')
    is_in_shopping_cart = CharFilter(method='is_in_shopping_cart_filter')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def is_favorited_filter(self, queryset, name, value):
        """Фильтрует рецепты, находящиеся в избранном."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited__owner=user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        """Фильтрует рецепты, находящиеся в списке покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping__owner=user)
        return queryset


class IngredientFilter(FilterSet):
    """Фильтерсет ингредиентов."""
    name = CharFilter(method='ingredient_filter')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def ingredient_filter(self, queryset, name, value):
        """Находит ингредиенты по вхождению в начало названия"""
        return queryset.filter(name__startswith=value)
