from django.db.models import Sum
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
from .serializers import (CustomUserSerializer, FavoriteSerializer,
                          IngredientSerializer, PostRecipeSerializer,
                          RecipeSerializer, ShoppingSerializer,
                          SubscribeSerializer, SubscribeWriteSerializer,
                          TagSerializer)


class CustomUserViewSet(UserViewSet):
    """Вьюсет пользователя."""
    queryset = User.objects.all()
    pagination_class = LimitPagination
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        """Переопределяет разрешения для эндпоинта '/me'."""
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super(CustomUserViewSet, self).get_permissions()

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        """Создаёт объекты подписки."""
        author = get_object_or_404(User, pk=self.kwargs.get('id'))
        data = {
            'author': author.id,
            'user': request.user.id
        }
        serializer = SubscribeWriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, **kwargs):
        """Удаляет объекты подписки."""
        author = get_object_or_404(User, pk=self.kwargs.get('id'))
        del_subscription, _ = Subscribe.objects.filter(
            author=author, user=request.user
        ).delete()
        if not del_subscription:
            raise ValidationError('Вы не подписаны на этого пользователя.')
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

    def create_obj(self, serializer_model, pk, request):
        """Создание объекта."""
        data = {'recipe': pk, 'owner': request.user.id}
        serializer = serializer_model(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, pk, owner):
        """Удаление объекта."""
        recipe = get_object_or_404(Recipe, pk=pk)
        del_subscription, _ = model.objects.filter(
            recipe=recipe, owner=owner
        ).delete()
        if not del_subscription:
            raise ValidationError('Этого рецепта нет в списке.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post',))
    def favorite(self, request, pk):
        return self.create_obj(
            serializer_model=FavoriteSerializer,
            pk=pk,
            request=request
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаляет объекты избранного."""
        return self.delete_obj(model=Favorite, pk=pk, owner=request.user)

    @action(
        detail=True, methods=['post']
    )
    def shopping_cart(self, request, pk):
        """Создаёт объекты списка покупок."""
        return self.create_obj(
            serializer_model=ShoppingSerializer,
            pk=pk,
            request=request
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удаляет объекты списка покупок."""
        return self.delete_obj(model=ShoppingCart, pk=pk, owner=request.user)

    @staticmethod
    def get_shopping_list(ingredients, owner):
        """Формирует содержимое файла со списком покупок."""
        header = (
            f'Список покупок.\nВладелец: {owner.first_name} '
            f'{owner.last_name}.\n'
        )
        shopping_list = '\n'.join(
            [
                f'- {ingredient["ingredient__name"]} '
                f' ({ingredient["ingredient__measurement_unit"]})'
                f' {ingredient["amount"]} '
                for ingredient in ingredients
            ]
        )
        return header + shopping_list

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
        shopping_list = self.get_shopping_list(
            ingredients=ingredients, owner=owner
        )
        filename = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
