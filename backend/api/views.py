from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import Subscribe, User
from api.filters import RecipesFilter
from api.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                        ShoppingCart, Tag)
from api.pagination import FoodgramPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CreateRecipeSerializer, IngredientSerializer,
                             MainRecipeSerializer, RecipeSerializer,
                             SubscribingSerializer, TagSerializer,
                             UsersSerializer)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Ingredient.objects.all()
    filter_backends = (filters.SearchFilter, )
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    pagination_class = None
    search_fields = ('^name', )


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, )
    pagination_class = FoodgramPagination
    permission_classes = (IsAuthorOrReadOnly, )
    filterset_class = RecipesFilter
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return MainRecipeSerializer
        return CreateRecipeSerializer

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, **kwargs):
        user = request.user
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
            favorite_recipe = user.favorite_user.filter(recipe=recipe)
            if not favorite_recipe.exists():
                return Response(
                    {'errors': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_recipe.delete()
            return Response(
                {'detail': 'Рецепт успешно удален из избранного.'},
                status=status.HTTP_204_NO_CONTENT
            )

        if not Recipe.objects.filter(id=kwargs.get('pk')).exists():
            return Response(
                {'errors': 'Рецепта не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = Recipe.objects.get(id=kwargs.get('pk'))

        if request.method == 'POST':
            serializer = RecipeSerializer(
                recipe, data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            if not user.favorite_user.filter(
                recipe=recipe
            ).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'errors': 'Рецепт уже добавлен в избранное.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        pagination_class=None
    )
    def shopping_cart(self, request, **kwargs):
        user = request.user
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=kwargs['pk'])
            shopping_cart = user.cart_user.filter(recipe=recipe)
            if not shopping_cart.exists():
                return Response(
                    {'errors': 'Рецепта нет в списке.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart.delete()
            return Response(
                {'detail': 'Рецепт удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT
            )

        if not Recipe.objects.filter(id=kwargs['pk']).exists():
            return Response(
                {'errors': 'Рецепта не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            recipe = Recipe.objects.get(id=kwargs.get('pk'))
            serializer = RecipeSerializer(
                recipe, data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            if not user.cart_user.filter(recipe=recipe).exists():
                ShoppingCart.objects.create(user=request.user, recipe=recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                {'errors': 'Рецепт уже находится в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__cart_recipe__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list(
                'ingredient__name',
                'total_amount',
                'ingredient__measurement_unit'
            )
        )
        list_for_file = []
        [list_for_file.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        response_file = HttpResponse(
            'Cписок покупок:\n' + '\n'.join(list_for_file),
            content_type='text/plain'
        )
        response_file['Content-Disposition'] = (
            'attachment; filename=shopping_cart.txt'
        )
        return response_file


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = FoodgramPagination
    permission_classes = (AllowAny,)
    serializer_class = UsersSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)

    @action(
        detail=False, methods=['get'],
        pagination_class=None,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = UsersSerializer(request.user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=FoodgramPagination
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscribingSerializer(
            page,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        pagination_class=FoodgramPagination,
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        user = request.user
        subscribtion = user.subscriber.filter(author=author)

        if request.method == 'POST':
            if subscribtion.exists():
                return Response(
                    {'errors': 'Нельзя подписаться повторно.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscribingSerializer(
                author, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)

            Subscribe.objects.create(
                user=request.user, author=author
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            if not subscribtion.exists():
                return Response(
                    {'errors': 'Подписки не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            get_object_or_404(
                Subscribe, user=request.user,
                author=author
            ).delete()
            return Response(
                {'detail': 'Отписка прошла успешно'},
                status=status.HTTP_204_NO_CONTENT
            )
