from django.conf import settings
from django.db.models.expressions import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            Tag, User)
from users.models import CustomUser, Subscribe

from .utils import Base64ImageField


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для записи в рецепт."""
    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта в краткой форме."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CreateCustomUserSerializer(UserSerializer):
    """Сериализатор пользователей, использующийся для записи."""

    class Meta:
        model = User
        fields = settings.USER_FIELDS + ('password',)
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        """Создаёт объект пользователя."""
        user = CustomUser(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователей, использующийся для чтения."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = settings.USER_FIELDS + ('is_subscribed',)

    def get_is_subscribed(self, obj):
        """
        Получает значение поля is_subscribed, которое указывает,
        подписан ли пользователь на автора.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class SubscribeSerializer(CustomUserSerializer):
    """Сериализатор подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        model = CustomUser
        fields = CustomUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes(self, obj):
        """Получает кверисет рецептов автора."""
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeShortSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        """Получает количество рецептов автора."""
        return obj.recipes.count()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов, использующийся для чтения."""
    is_favorited = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)
    ingredients = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        """Получает список ингредиентов в развёрнутом виде."""
        ingredients = obj.ingredients.values(
            'id', 'name', 'measurement_unit',
            amount=F('recipeingredient__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        """
        Получает значение поля is_favorited, указывающего,
        находится ли рецепт в избранном.
        """
        user = self.context.get('request').user
        return user.is_authenticated and user.favorited.filter(
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Получает значение поля is_in_shopping_cart, указывающего,
        находится ли рецепт в списке покупок.
        """
        user = self.context.get('request').user
        return user.is_authenticated and user.shopping.filter(
            recipe=obj
        ).exists()


class PostRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов, использующийся для записи."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'author', 'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        """Проверяет ингредиенты на корректность."""
        if not value:
            raise ValidationError('Не хватает ингредиентов.')
        ingredients = []
        for ingredient in value:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise ValidationError('Несуществующий ингредиент.')
            if ingredient in ingredients:
                raise ValidationError('Ингредиенты не должны повторяться.')
            if ingredient['amount'] <= 0:
                raise ValidationError('Недостаточное количество ингредиента.')
            ingredients.append(ingredient)
        return value

    def validate_tags(self, value):
        """Проверяет теги на корректность."""
        if not value:
            raise ValidationError('Нужен хотя бы один тег.')
        tags = []
        for tag in value:
            if not Tag.objects.filter(id=tag.id).exists():
                raise ValidationError('Несуществующий тег.')
            if tag in tags:
                raise ValidationError('Теги не должны повторяться.')
            tags.append(tag)
        return value

    def validate(self, attrs):
        """Проверяет, указаны ли в запросе теги и ингредиенты."""
        if not attrs.get('ingredients'):
            raise ValidationError('Не указаны ингредиенты.')
        if not attrs.get('tags'):
            raise ValidationError('Не указаны теги.')
        return attrs

    def create_recipeingredient(self, recipe, ingredients):
        """Создаёт связи между рецептом и ингредиентами."""
        ingredients_list = [
            RecipeIngredient(
                ingredient=get_object_or_404(Ingredient, pk=item['id']),
                recipe=recipe,
                amount=item['amount']
            ) for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        """Создаёт объект рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_recipeingredient(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет объект рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_recipeingredient(recipe=instance, ingredients=ingredients)
        return instance

    def to_representation(self, instance):
        """Передаёт данные в сериализатор, использующийся для чтения."""
        request = self.context.get('request')
        context = {'request': request}
        serializer = RecipeSerializer(instance, context=context)
        return serializer.data
