from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import EMAIL_MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(max_length=EMAIL_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Пользователи'
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscriber',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписан',
        related_name='subscribing',
    )

    def __str__(self):
        return f'{self.user.username} - подписан на {self.author.username}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            )
        ]
        verbose_name = 'Подписка на авторов'
        verbose_name_plural = 'Подписки на авторов'
