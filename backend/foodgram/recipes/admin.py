from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag,
                     ShoppingCart, Tag)


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


class TagInline(admin.TabularInline):
    model = RecipeTag
    extra = 0
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author'
    )
    list_filter = (
        'name',
        'author',
        'tags'
    )
    readonly_fields = ('in_favorites',)
    inlines = (IngredientInline, TagInline)

    @admin.display(description='Число добавлений в избранное')
    def in_favorites(self, instance):
        return instance.favorited.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'recipe'
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'recipe'
    )
