from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import MyUserViewSet

from .views import (IngredientViewSet, RecipeViewSet,  # SubscriptionViewSet,
                    TagViewSet)

router = DefaultRouter()
router.register(r'users', MyUserViewSet, basename='user')
router.register(r'ingredients', IngredientViewSet)
router.register(r'tags', TagViewSet)
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
