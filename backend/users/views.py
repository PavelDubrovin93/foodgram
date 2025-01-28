
from api.pagination import MyPageNumberPaginator
from api.permissions import OwnerOrReadOnly
from api.serializer import AvatarSerializer, SubscriptionSerializer
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription, User


class MyUserViewSet(UserViewSet):

    pagination_class = MyPageNumberPaginator

    @action(["get", "put", "patch", "delete"],
            detail=False,
            permission_classes=[IsAuthenticated]
            )
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        elif request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)
        elif request.method == "DELETE":
            return self.destroy(request, *args, **kwargs)

    @action(detail=False,
            methods=['PUT', 'DELETE'],
            url_path='me/avatar',
            permission_classes=[OwnerOrReadOnly]
            )
    def upload_avatar(self, request):
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response({"error": "bad request"},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'],
            detail=False,
            url_path='subscriptions',
            permission_classes=[IsAuthenticated]
            )
    def subscribed(self, request, *args, **kwargs):
        queryset = Subscription.objects.filter(subscriber=request.user)
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

            if Subscription.objects.filter(
                subscriber=request.user,
                subscribed_to=subscribed_to
            ).exists():
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
