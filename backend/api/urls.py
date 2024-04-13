from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register('users', views.UsersViewSet, basename='users')
router.register(
    'ingredients', views.IngredientsViewSet, basename='ingredients'
)
router.register('recipes', views.RecipesViewSet, basename='recipes')
router.register('tags', views.TagsViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
