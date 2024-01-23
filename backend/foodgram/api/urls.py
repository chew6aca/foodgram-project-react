from django.urls import include, path
from rest_framework import routers

from .views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet)

router = routers.DefaultRouter()
router.register(
    'ingredients', viewset=IngredientViewSet, basename='ingredients'
)
router.register('tags', viewset=TagViewSet, basename='tags')
router.register('recipes', viewset=RecipeViewSet, basename='recipes')
router.register('users', viewset=CustomUserViewSet, basename='users')
urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]
