from django.contrib import admin
from django.db.models import Count

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag

admin.site.register(Tag)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'tags',
        'favorite_count'
    )
    search_fields = ('name', 'author')
    filter_horizontal = ('tags',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            favorite_count=Count('favorite')
        )
        return queryset

    def favorite_count(self, obj):
        return obj.favorite_count


admin.site.register(Recipe, RecipeAdmin)


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)


admin.site.register(Ingredient)
