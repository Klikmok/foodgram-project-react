# flake8: noqa
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from users.models import Subscribe, User


class UserRetrieveSerializer(UserSerializer):
    """Информация об отдельном пользователе для настроек djoser."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Subscribe.objects.filter(
                user=request.user, author=obj
            ).exists()
        )


class UsersSerializer(UserSerializer):
    """Cписок всех пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        if (
            self.context.get('request')
            and not self.context['request'].user.is_anonymous
        ):
            return Subscribe.objects.filter(
                user=self.context['request'].user,
                author=obj
            ).exists()
        return False


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'password'
        )
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate(self, obj):
        disalowed_usernames = [
            'me', 'username', 'following'
            'subscriptions', 'subscribe'
        ]
        if self.initial_data.get('username') in disalowed_usernames:
            raise serializers.ValidationError(
                {'username': 'Вы не можете использовать такой username.'}
            )
        return obj


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except django_exceptions.ValidationError as error:
            raise serializers.ValidationError(
                {'new_password': list(error.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль.'}
            )
        if (
            validated_data['current_password']
            == validated_data['new_password']
        ):
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль не должен совпадать с текущим.'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'image', 'cooking_time'
        )


class SubscriptionsSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(
                user=self.context['request'].user,
                author=obj
            ).exists()
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeSerializer(
            recipes,
            read_only=True,
            many=True
        )
        return serializer.data


class SubscribeAuthorSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )

    def validate(self, obj):
        if (self.context['request'].user == obj):
            raise serializers.ValidationError({'errors': 'Ошибка подписки'})
        return obj

    def get_is_subscribed(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Subscribe.objects.filter(
                user=self.context['request'].user,
                author=obj
            ).exists()
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name',
            'measurement_unit', 'amount'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UsersSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipes')
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags',
            'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image',
            'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(
                user=self.context['request'].user,
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and ShoppingCart.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists()
        )


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UsersSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    image = Base64ImageField()
    ingredients = RecipeIngredientCreateSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients',
            'tags', 'image',
            'name', 'text',
            'cooking_time', 'author'
        )
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},
            'tags': {'required': True, 'allow_blank': False},
            'ingredients': {'required': True, 'allow_blank': False},
            'text': {'required': True, 'allow_blank': False},
            'cooking_time': {'required': True},
            'image': {'required': True, 'allow_blank': False},
        }

    def validate(self, obj):
        for field in ['name', 'text', 'cooking_time', 'ingredients', 'tags']:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'{field} - обязательное поле.'
                )
        inrgedient_id_list = [item['id'] for item in obj.get('ingredients')]
        for id in inrgedient_id_list:
            if not Ingredient.objects.filter(
                pk=id
            ).exists():
                raise serializers.ValidationError(
                    'Ингредиента не существует.'
                )
        unique_ingredient_id_list = set(inrgedient_id_list)
        if len(inrgedient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        tags_list = obj.get('tags')
        unique_tags_list = set(tags_list)
        if len(tags_list) != len(unique_tags_list):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        return obj

    @transaction.atomic
    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        RecipeIngredient.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data
