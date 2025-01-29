from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User
from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import MyPageNumberPaginator
from .permissions import OwnerOrReadOnly
from .serializer import (FavoriteSerializer, IngredientSerializer,
                         RecipeSerializer, ShoppingCartSerializer,
                         ShortLinkSerializer, TagSerializer,
                         AvatarSerializer, SubscriptionSerializer)


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
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
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
            if user.favorite.filter(recipe=recipe).exists():
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
        if not user.favorite.filter(recipe=recipe).exists():
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
            if user.shopping_cart.filter(recipe=recipe).exists():
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
        if not user.shopping_cart.filter(recipe=recipe).exists():
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

        recipe_ids = request.user.shopping_cart.all().values_list(
            'recipe',
            flat=True
        )

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


class MyUserViewSet(UserViewSet):

    pagination_class = MyPageNumberPaginator

    @action(['get', 'put', 'patch', 'delete'],
            detail=False,
            permission_classes=[IsAuthenticated]
            )
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == 'GET':
            return self.retrieve(request, *args, **kwargs)
        elif request.method == 'PUT':
            return self.update(request, *args, **kwargs)
        elif request.method == 'PATCH':
            return self.partial_update(request, *args, **kwargs)
        elif request.method == 'DELETE':
            return self.destroy(request, *args, **kwargs)

    @action(['put', 'delete'],
            detail=False,
            url_path='me/avatar',
            permission_classes=[OwnerOrReadOnly]
            )
    def upload_avatar(self, request):
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response({'error': 'bad request'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'],
            detail=False,
            url_path='subscriptions',
            permission_classes=[IsAuthenticated]
            )
    def subscribed(self, request, *args, **kwargs):
        queryset = request.user.subscriptions.all()
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            context={'request': request},
            many=True)
        return self.get_paginated_response(serializer.data)

    @action(['post', 'delete'],
            detail=True,
            url_path='subscribe',
            permission_classes=[IsAuthenticated]
            )
    def subscribe_change(self, request, id=None):
        subscribed_to = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            if subscribed_to == request.user:
                return Response(
                    {'detail': 'Нельзя подписываться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if request.user.subscriptions.filter(
                    subscribed_to=subscribed_to).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionSerializer(
                data={
                    'subscriber': request.user.email,
                    'subscribed_to': subscribed_to.email
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(
            Subscription,
            subscriber=request.user,
            subscribed_to=subscribed_to
        )
        subscription.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
