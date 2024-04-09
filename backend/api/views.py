# flake8: noqa
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscribe, User

from .filters import RecipeCustomFilter
from .models import (
    Favorite, Ingredient, Recipe,
    RecipeIngredient, ShoppingCart, Tag
)
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    SubscribeAuthorSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    UsersSerializer,
    SetPasswordSerializer,
    SubscriptionsSerializer,
    UserCreateSerializer,
)


class UsersViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return UsersSerializer
        return UserCreateSerializer

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
        detail=False, methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(
            {'detail': 'Пароль успешно изменен!'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=CustomPagination
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        pagination_class=CustomPagination,
    )
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])
        user = request.user
        subscribtion = Subscribe.objects.filter(
            user=request.user,
            author=author
        )
        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if subscribtion.exists():
                return Response(
                    {'errors': 'Нельзя подписаться повторно.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscribeAuthorSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=request.user, author=author)
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


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (filters.SearchFilter, )
    pagination_class = None
    search_fields = ('^name', )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, )
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly, )
    filterset_class = RecipeCustomFilter
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']

    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, **kwargs):
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=kwargs['pk'])
            if not Favorite.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.get(
                user=request.user,
                recipe=recipe
            ).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из избранного.'},
                status=status.HTTP_204_NO_CONTENT
            )

        if not Recipe.objects.filter(id=kwargs['pk']).exists():
            return Response(
                {'errors': 'Рецепта не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = Recipe.objects.get(id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeSerializer(
                recipe, data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(
                user=request.user,
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
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=kwargs['pk'])
            if not ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепта нет в списке.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            get_object_or_404(
                ShoppingCart,
                user=request.user,
                recipe=recipe
            ).delete()
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
            recipe = Recipe.objects.get(id=kwargs['pk'])
            serializer = RecipeSerializer(
                recipe, data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            if not ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():

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
            .filter(recipe__shopping_recipe__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list(
                'ingredient__name', 'total_amount',
                'ingredient__measurement_unit'
            )
        )
        list_for_file = []
        [list_for_file.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse(
            'Cписок покупок:\n' + '\n'.join(list_for_file),
            content_type='text/plain'
        )
        file['Content-Disposition'] = (
            'attachment; filename=shopping_cart.txt'
        )
        return file
