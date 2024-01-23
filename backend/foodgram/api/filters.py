from django.db.models import BooleanField, ExpressionWrapper, Q
from django_filters import FilterSet
from django_filters.filters import CharFilter, ModelMultipleChoiceFilter

from recipes.models import Ingredient, Recipe, Tag

TRUE_VALUES = ('True', 'true', '1')


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
        if value in TRUE_VALUES and not user.is_anonymous:
            return queryset.filter(favorited__owner=user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        """Фильтрует рецепты, находящиеся в списке покупок."""
        user = self.request.user
        if value in TRUE_VALUES and not user.is_anonymous:
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
        expression = Q(name__startswith=value)
        is_match = ExpressionWrapper(expression, output_field=BooleanField())
        return queryset.filter(
            Q(name__startswith=value) | Q(name__icontains=value)
        ).order_by(is_match.desc())
