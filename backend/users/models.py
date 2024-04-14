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
        verbose_name='подписчик',
        related_name='subscriber',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='подписан',
        related_name='subscribing',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            )
        ]
        ordering = ['-id']
        verbose_name = 'Подписка на авторов'
        verbose_name_plural = 'Подписки на авторов'

    def __str__(self):
        return f'На {self.author.username} подписан {self.user.username}'
