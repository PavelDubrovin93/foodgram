from django.contrib import admin

from .models import MyUser, Subscription

admin.site.register(MyUser)
admin.site.register(Subscription)
