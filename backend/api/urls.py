from rest_framework import routers
from api.views import (
    TagsViewSet, RecipesViewSet, IngredientsViewSet, UsersViewSet
)
from django.urls import path, include

router = routers.DefaultRouter()

router.register('users', UsersViewSet, basename='users')
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
