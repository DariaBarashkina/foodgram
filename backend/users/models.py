from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

from users.constants import MAX_EMAIL_LENGTH, MAX_USERNAME_LENGTH


class User(AbstractUser):
    """Модель пользователя. Использует email как основной идентификатор."""

    email = models.EmailField(
        'Email', max_length=MAX_EMAIL_LENGTH, unique=True
    )
    username = models.CharField(
        'Username', max_length=MAX_USERNAME_LENGTH, unique=True
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)

    avatar = models.ImageField(
        'Аватар', upload_to='users/', null=True, blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки пользователей."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на себя')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} → {self.author}'
