# flake8: noqa
from django.urls import path, include
from rest_framework import routers
from api.views import TagViewSet, RecipeViewSet, IngredientViewSet, UsersViewSet

router = routers.DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UsersViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
