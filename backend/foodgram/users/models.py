from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""
    username = models.CharField(
        'Никнейм',
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                r'^[\w.@+-]+\Z',
                'Вы не можете зарегестрировать пользователя с таким именем.'
            )
        ]
    )
    password = models.CharField('Пароль', max_length=150)
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    REQUIRED_FIELDS = ('first_name', 'last_name', 'email')


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
