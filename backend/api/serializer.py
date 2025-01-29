import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import SlugRelatedField
from users.models import Subscription, User

from .pagination import MyPageNumberPaginator
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)

MIN_AMOUNT = 1
MAX_AMOUNT = 32000
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class MyUserSerializer(UserSerializer):

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.subscriptions.filter(subscribed_to=obj).exists()
        return False


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class TagSerializer(serializers.ModelSerializer):
    """Serializer для модели Tag."""
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Serializer для связаной модели Recipe и Ingredient."""
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AddIngredientSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):

    ingredients = AddIngredientSerializer(
        many=True,
        write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    image = Base64ImageField()
    author = MyUserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'отсутствует ингредиент!'})
        ingredients_set = set()
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, name=item['id'])
            if ingredient in ingredients_set:
                raise ValidationError(
                    {'ingredients': 'Ингредиенты повторяются!'})
            ingredients_set.update(ingredient)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError(
                {'tags': 'отсутствует таг!'})
        tags_set = set()
        for tag in tags:
            if tag in tags_set:
                raise ValidationError(
                    {'tags': 'Теги повторяются!'})
            tags_set.update(tag)
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['ingredients'] = IngredientRecipeSerializer(
            instance.recipe_ingredients.all(), many=True).data
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True).data
        return representation

    def add_tags_ingredients(self, ingredients, tags, model):
        bulk_list = []
        for ingredient in ingredients:
            bulk_list.append(
                recipe=model,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
        IngredientRecipe.objects.bulk_create(bulk_list)
        model.tags.set(tags)

    def create(self, validated_data):
        author = self.context['request'].user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = author
        recipe = super().create(validated_data)
        self.add_tags_ingredients(ingredients, tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        try:
            ingredients = validated_data.pop('ingredients')
        except KeyError:
            raise ValidationError({'ingredients': 'Отсутствует ключ'})
        try:
            tags = validated_data.pop('tags')
        except KeyError:
            raise ValidationError({'tags': 'Отсутствует ключ'})
        instance.ingredients.clear()
        self.add_tags_ingredients(ingredients, tags, instance)
        return super().update(instance, validated_data)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_anonymous:
            return obj.favorite.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_anonymous:
            return obj.shopping_cart.filter(user=user).exists()
        return True


class ShortLinkSerializer(serializers.HyperlinkedModelSerializer):
    short_link = serializers.HyperlinkedIdentityField(
        view_name='recipe-detail', lookup_field='pk'
    )

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        url = representation.pop('short_link').replace('/api', '')
        representation['short-link'] = url
        return representation


class SubscriptionSerializer(serializers.ModelSerializer):

    subscriber = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    subscribed_to = SlugRelatedField(
        slug_field='email',
        queryset=User.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('subscriber', 'subscribed_to',)

    def create(self, validated_data):
        subscription = Subscription.objects.create(
            subscriber=self.context['request'].user,
            subscribed_to=validated_data.pop('subscribed_to')
        )

        return subscription

    def to_representation(self, instance):
        representation = SubUserSerializer(
            instance.subscribed_to,
            context=self.context).data
        return representation


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubRecipeSerializer(serializers.ModelSerializer):
    class Meta():
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubUserSerializer(MyUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(MyUserSerializer.Meta):
        pagination_class = MyPageNumberPaginator
        fields = MyUserSerializer.Meta.fields + (
            'recipes_count',
            'recipes',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return SubRecipeSerializer(recipes, many=True).data


class FavoriteSerializer(serializers.ModelSerializer):

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def create(self, validated_data):

        create_some_one = Favorite.objects.create(
            user=self.context['request'].user,
            recipe=validated_data.pop('recipe')
        )
        return create_some_one

    def to_representation(self, instance):

        representation = SubRecipeSerializer(
            instance.recipe,
            context=self.context).data

        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def create(self, validated_data):

        create_some_one = ShoppingCart.objects.create(
            user=self.context['request'].user,
            recipe=validated_data.pop('recipe')
        )
        return create_some_one

    def to_representation(self, instance):

        representation = SubRecipeSerializer(
            instance.recipe,
            context=self.context).data

        return representation
