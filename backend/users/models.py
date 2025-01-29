from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_CHARFIELD_LENGHT = 150


class MyUser(AbstractUser):
    avatar = models.ImageField(
        'Аватар',
        null=True,
        default=None
    )
    email = models.CharField(
        unique=True,
        max_length=MAX_CHARFIELD_LENGHT,
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_CHARFIELD_LENGHT
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_CHARFIELD_LENGHT
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta(AbstractUser.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-id']

    def __str__(self):
        return f'{self.email}'


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Кто подписался'
    )
    subscribed_to = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='На кого подписались'
    )

    class Meta:
        unique_together = ('subscriber', 'subscribed_to')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']

    def __str__(self):
        return f'{self.user} подписался на {self.recipe}'
