from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import MyPageNumberPaginator
from .permissions import OwnerOrReadOnly
from .serializer import (FavoriteSerializer, IngredientSerializer,
                         RecipeSerializer, ShoppingCartSerializer,
                         ShortLinkSerializer, TagSerializer)


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter, )
    search_fields = ('^name',)


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    """Функция для модели тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет модели Recipe: [GET, POST, DELETE, PATCH]."""
    queryset = Recipe.objects.all()
    permission_classes = (OwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, )
    pagination_class = MyPageNumberPaginator
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            url_path='favorite')
    def favorite_change(self, request, pk=None):

        recipe = get_object_or_404(Recipe, id=pk)
        user = self.request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user,
                                       recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = FavoriteSerializer(
                data={
                    'user': user,
                    'recipe': recipe.id
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not Favorite.objects.filter(user=user,
                                       recipe=recipe).exists():
            return Response({'errors': 'Объект не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        Favorite.objects.get(recipe=recipe).delete()
        return Response('Рецепт успешно удалён из избранного.',
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            url_path='shopping_cart')
    def shopping_carg_change(self, request, pk=None):

        recipe = get_object_or_404(Recipe, id=pk)
        user = self.request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user,
                                       recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShoppingCartSerializer(
                data={
                    'user': request.user,
                    'recipe': recipe.id
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response({'errors': 'Объект не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        ShoppingCart.objects.get(recipe=recipe).delete()
        return Response('Рецепт успешно удалён из избранного.',
                        status=status.HTTP_204_NO_CONTENT)

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):

        recipe_ids = ShoppingCart.objects.filter(
            user=request.user
        ).values_list('recipe', flat=True)

        queryset = (
            IngredientRecipe.objects
            .filter(recipe_id__in=recipe_ids)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        buffer = BytesIO()

        for result in queryset:
            ingredient = result['ingredient__name']
            total_amount = result['total_amount']
            measurment_unit = result['ingredient__measurement_unit']
            buffer.write(
                f'{ingredient}:{total_amount}'
                f'{measurment_unit}.\n'.encode('utf-8')
            )

        buffer.seek(0)
        response = FileResponse(
            buffer,
            as_attachment=True,
            content_type='text/plain',
            filename='shopping_list.txt'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def getlink(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = ShortLinkSerializer(recipe, context={'request': request})
        return Response(serializer.data)
