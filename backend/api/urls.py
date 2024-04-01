from django.urls import path, include
from rest_framework import routers
from api.views import TagViewSet, RecipeViewSet, IngredientViewSet, UserViewSet

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(
    r'ingredients', IngredientViewSet, basename='ingredients')
router.register(
    r'users', UserViewSet, basename='users'
)

api_patterns = [
    path('', include(router.urls)),
    path('users/', include('users.urls')),

]

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
