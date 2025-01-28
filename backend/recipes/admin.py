from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag

admin.site.register(Tag)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name'
    )
    search_fields = ('name', 'author')
    filter_vertical = ('tags',)


admin.site.register(Recipe, RecipeAdmin)


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register(Ingredient)
