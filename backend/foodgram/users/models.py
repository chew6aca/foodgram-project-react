from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from core.constants import NAME_LEN, PASSWORD_LEN, SLICE_LEN


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')
    USERNAME_FIELD = 'email'
    username = models.CharField(
        'Никнейм',
        max_length=NAME_LEN,
        unique=True,
        validators=[
            UnicodeUsernameValidator()
        ]
    )
    password = models.CharField('Пароль', max_length=PASSWORD_LEN)
    email = models.EmailField(
        'Электронная почта',
        unique=True
    )
    first_name = models.CharField('Имя', max_length=NAME_LEN)
    last_name = models.CharField('Фамилия', max_length=NAME_LEN)

    def __str__(self):
        return self.username[:SLICE_LEN]


class Subscribe(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='Вы уже подписаны на этого пользователя.'
            )
        ]
