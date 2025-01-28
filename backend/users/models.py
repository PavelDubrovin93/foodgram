from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    avatar = models.ImageField(
        null=True,
        default=None
    )
    email = models.CharField(
        unique=True,
        max_length=150,
    )
    first_name = models.CharField(
        max_length=150
    )
    last_name = models.CharField(
        max_length=150
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']


User = MyUser


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        unique_together = ('subscriber', 'subscribed_to')
