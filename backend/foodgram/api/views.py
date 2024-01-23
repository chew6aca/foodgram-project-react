from django.db.models import Sum
from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, User)
from users.models import Subscribe

from .filters import IngredientFilter, RecipeModelFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrIsAdminOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          PostRecipeSerializer, RecipeShortSerializer,
                          RecipeSerializer, SubscribeSerializer, TagSerializer)
from .utils import get_shopping_list


class CustomUserViewSet(UserViewSet):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    pagination_class = LimitPagination
    serializer_class = CustomUserSerializer

    @action(
        methods=["get", "put", "patch", "delete"],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        """Обрабатывает запросы к эндпоинту /me"""
        return super().me(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        """Создаёт и удаляет подписки."""
        author = get_object_or_404(User, pk=self.kwargs.get('id'))
        user = request.user
        if author == user:
            raise ValidationError('Нельзя подписаться на самого себя.')
        if request.method == 'POST':
            serializer = SubscribeSerializer(
                author, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            try:
                Subscribe.objects.create(author=author, user=user)
            except IntegrityError:
                raise ValidationError(
                    'Вы уже подписаны на этого пользователя.'
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            subscribtion = get_object_or_404(
                Subscribe, author=author, user=user
            )
        except Exception:
            raise ValidationError('Вы не подписаны на этого пользователя.')
        subscribtion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Отображает подписки пользователя."""
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов."""
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeModelFilter
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    permission_classes = (IsAuthorOrIsAdminOrReadOnly,)

    def get_serializer_class(self):
        """Возвращает нужный сериализатор, в зависимости от типа запроса."""
        if self.request.method == 'GET':
            return RecipeSerializer
        return PostRecipeSerializer

    def perform_create(self, serializer):
        """Создаёт рецепт."""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """Обновляет рецепт."""
        serializer.save(author=self.request.user)

    def create_obj(self, model, pk, owner):
        """Создание объекта."""
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
        except Exception:
            raise ValidationError('Такого рецепта не существует.')
        if model.objects.filter(recipe=recipe, owner=owner).exists():
            raise ValidationError('Этот рецепт был добавлен ранее.')
        model.objects.create(recipe=recipe, owner=owner)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, pk, owner):
        """Удаление объекта."""
        recipe = get_object_or_404(Recipe, pk=pk)
        try:
            obj = get_object_or_404(
                model, recipe=recipe, owner=owner
            )
        except Exception:
            raise ValidationError('Этого рецепта нет в списке.')
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', 'delete']
    )
    def favorite(self, request, pk):
        """Создаёт и удаляет объекты избранного."""
        owner = request.user
        if request.method == 'DELETE':
            return self.delete_obj(pk=pk, owner=owner, model=Favorite)
        return self.create_obj(pk=pk, owner=owner, model=Favorite)

    @action(
        detail=True, methods=['post', 'delete']
    )
    def shopping_cart(self, request, pk):
        """Создаёт и удаляет объекты списка покупок."""
        owner = request.user
        if request.method == 'DELETE':
            return self.delete_obj(pk=pk, owner=owner, model=ShoppingCart)
        return self.create_obj(pk=pk, owner=owner, model=ShoppingCart)

    @action(detail=False)
    def download_shopping_cart(self, request):
        """Даёт список покупок в виде тестового документа."""
        owner = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping__owner=owner
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        )
        shopping_list = get_shopping_list(ingredients, owner)
        filename = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
