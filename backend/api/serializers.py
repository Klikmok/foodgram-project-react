from users.models import User, Subscribe
from rest_framework import serializers
from drf_base64.fields import Base64ImageField
from djoser.serializers import UserSerializer
from django.db import transaction

from .models import (
    ShoppingCart, RecipeIngredient, Ingredient, Tag, Favorite, Recipe
)


class UsersSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'password'
        ]
        read_only_fields = ("is_subscribed",)
        write_only_fields = ('password',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        if not (
            request
            and not request.user.is_anonymous
        ):
            return False
        user = request.user
        return Subscribe.objects.filter(
            user=user,
            author=obj
        ).exists()

    def validate(self, obj):
        for field in ['password', 'email', 'last_name', 'first_name']:
            if field not in self.initial_data:
                raise serializers.ValidationError(
                    {f'{field}': 'Обязательное поле.'}
                )
        return obj

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name',
            'measurement_unit', 'amount'
        )


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class MainRecipeSerializer(serializers.ModelSerializer):
    author = UsersSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True, many=True, source='recipes'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags',
            'name', 'image',
            'text', 'cooking_time',
            'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and Favorite.objects.filter(
                user=user,
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(
                user=user,
                recipe=obj
            ).exists()
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    author = UsersSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    image = Base64ImageField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients',
            'tags', 'image',
            'name', 'text',
            'cooking_time', 'author'
        )

    def validate(self, obj):
        for field in [
            'name', 'text', 'cooking_time', 'ingredients', 'tags', 'image'
        ]:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'{field} - обязательное поле.'
                )
        inrgedients_id_list = [item['id'] for item in obj.get('ingredients')]
        for id in inrgedients_id_list:
            if not Ingredient.objects.filter(
                pk=id
            ).exists():
                raise serializers.ValidationError(
                    'Ингредиента не существует.'
                )
        unique_ingredients_id_list = set(inrgedients_id_list)
        if len(inrgedients_id_list) != len(unique_ingredients_id_list):
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
    def create_tags_and_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                amount=ingredient.get('amount'),
                ingredient=Ingredient.objects.get(pk=ingredient.get('id')),
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            **validated_data
        )
        self.create_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        RecipeIngredient.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredients.all()).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_tags_and_ingredients(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return MainRecipeSerializer(
            instance,
            context=self.context
        ).data


class SubscribingSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeSerializer(
            recipes,
            read_only=True,
            many=True
        )
        return serializer.data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        if not (
            request
            and not request.user.is_anonymous
        ):
            return False
        user = request.user
        return Subscribe.objects.filter(
            user=user,
            author=obj
        ).exists()
