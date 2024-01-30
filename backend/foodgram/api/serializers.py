from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Ingredient, Favorite, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, User)
from users.models import Subscribe


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
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError(
                'Недостаточное количество ингредиента.'
            )
        return value


class IngredientReadSerializer(RecipeIngredientSerializer):
    """Сериализатор ингредиентов для чтения в рецепте."""
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta(RecipeIngredientSerializer.Meta):
        fields = RecipeIngredientSerializer.Meta.fields + (
            'name', 'measurement_unit'
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта в краткой форме."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей, использующийся для чтения."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed'
            )

    def get_is_subscribed(self, obj):
        """
        Получает значение поля is_subscribed, которое указывает,
        подписан ли пользователь на автора.
        """
        request = self.context.get('request')
        return bool(
            request and
            request.user.is_authenticated and
            Subscribe.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )


class SubscribeSerializer(CustomUserSerializer):
    """Сериализатор подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        model = User
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
            try:
                recipes = recipes[:int(recipes_limit)]
            except Exception:
                raise ValidationError(
                    'В recipes_limit должны быть только цифры.'
                )
        serializer = RecipeShortSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        """Получает количество рецептов автора."""
        return obj.recipes.count()

    def validate(self, attrs):
        author = self.instance
        user = self.context.get('request').user
        if author == user:
            raise ValidationError('Нельзя подписаться на самого себя.')
        if Subscribe.objects.filter(author=author, user=user).exists():
            raise ValidationError('Вы уже подписаны на этого пользователя.')
        return attrs

    def update(self, instance, validated_data):
        user = self.context.get('request').user
        Subscribe.objects.create(author=instance, user=user)
        return instance


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов, использующийся для чтения."""
    is_favorited = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientReadSerializer(
        many=True, read_only=True, source='amount_ingredient'
    )
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

    def get_is_favorited(self, obj):
        """
        Получает значение поля is_favorited, указывающего,
        находится ли рецепт в избранном.
        """
        request = self.context.get('request')
        return bool(
            request and
            request.user.is_authenticated and
            request.user.favorited.filter(
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """
        Получает значение поля is_in_shopping_cart, указывающего,
        находится ли рецепт в списке покупок.
        """
        request = self.context.get('request')
        return bool(
            request and
            request.user.is_authenticated and
            request.user.shopping.filter(
                recipe=obj
            ).exists()
        )


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

    def validate(self, attrs):
        """Проверяет, указаны ли в запросе теги и ингредиенты."""
        if not attrs.get('image'):
            raise ValidationError('Не хватает изображения.')
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise ValidationError('Не указаны ингредиенты.')
        ingredients_list = [
            ingredient['ingredient'].id for ingredient in ingredients
        ]
        if len(ingredients_list) != len(set(ingredients_list)):
            raise ValidationError('Ингредиенты не должны повторяться.')
        tags = attrs.get('tags')
        if not tags:
            raise ValidationError('Не указаны теги.')
        if len(tags) != len(set(tags)):
            raise ValidationError('Теги не должны повторяться.')
        return attrs

    def create_recipeingredient(self, recipe, ingredients):
        """Создаёт связи между рецептом и ингредиентами."""
        ingredients_list = [
            RecipeIngredient(
                ingredient=item['ingredient'],
                recipe=recipe,
                amount=item['amount']
            ) for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        """Создаёт объект рецепта."""
        validated_data['author'] = self.context.get('request').user
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
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class BaseFavoriteShoppingSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для создания записей избранного и списка покупок.
    """
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        abstract = True
        fields = ('recipe',)
        read_only_fields = ('recipe',)
        model = None

    def validate(self, attrs):
        recipe = attrs['recipe']
        owner = self.context.get('request').user
        if self.Meta.model.objects.filter(recipe=recipe, owner=owner).exists():
            raise ValidationError('Этот рецепт уже есть в списке.')
        return attrs

    def create(self, validated_data):
        owner = self.context.get('request').user
        recipe = validated_data.get('recipe')
        return self.Meta.model.objects.create(recipe=recipe, owner=owner)

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(BaseFavoriteShoppingSerializer):
    """Сериализатор избранного."""

    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = Favorite


class ShoppingSerializer(BaseFavoriteShoppingSerializer):
    """Сериализатор списка покупок."""

    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = ShoppingCart
