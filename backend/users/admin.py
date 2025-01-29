from django.contrib import admin

from .models import User, Subscription

admin.site.register(Subscription)


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name'
    )
    search_fields = ('email', 'username')


admin.site.register(User, UserAdmin)
