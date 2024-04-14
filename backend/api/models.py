from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from users.models import User
from api.constants import MAX_FIELD_NUM, MAX_FIELDS_LENGHT, MIN_FIELD_NUM


class Tag(models.Model):
    name = models.CharField(
        'Название тега',
        max_length=MAX_FIELDS_LENGHT
    )
    color = models.CharField(
        'Цвет тега',
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Цвет некорректен.'
            )
        ],
        max_length=7,
        null=True,

    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=MAX_FIELDS_LENGHT,
        null=True,
        unique=True,
    )

    class Meta:
        ordering = ['-slug']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=MAX_FIELDS_LENGHT
    )
    measurement_unit = models.CharField(
        'Единица измерения игредиента',
        max_length=MAX_FIELDS_LENGHT
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    name = models.CharField(
        'Название рецепта.',
        max_length=MAX_FIELDS_LENGHT
    )
    text = models.TextField(
        'Описание рецепта.'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[
            MaxValueValidator(
                MAX_FIELD_NUM,
                message='Время готовки не должно быть слишком долгим!'
            ),
            MinValueValidator(
                MIN_FIELD_NUM,
                message='Время готовки не должно быть меньше 1!'
            )
        ]
    )
    image = models.ImageField(
        'Картинка',
        blank=True,
        upload_to='recipes/',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        through_fields=('recipe', 'ingredient'),
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_user',
        verbose_name='Добавил в список'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart_recipe',
        verbose_name='Рецепт в списке'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        ordering = ['-id']

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        default=MIN_FIELD_NUM,
        validators=[
            MaxValueValidator(
                MAX_FIELD_NUM,
                message='Количество не должно быть слишком большим!'
            ),
            MinValueValidator(
                MIN_FIELD_NUM,
                message='Количество не должно быть меньше 1!'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_combination'
            )
        ]
        ordering = ['-id']


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_user',
        verbose_name='добавил в избранное'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='избранный рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        ordering = ['-id']

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
