from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):

    name = models.CharField(
        db_index=True,
        max_length=150,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=150,
        verbose_name='Единица измерения',
    )

    def __str__(self):
        return self.name


class Tag(models.Model):

    name = models.CharField(
        max_length=200, unique=True,)
    slug = models.SlugField(
        max_length=200, unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиент',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Название тега',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Опишите приготовление рецепта'
    )
    name = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1, 'Минимальное время приготовления')],
        verbose_name='Время приготовления',
        help_text='Укажите время приготовления рецепта в минутах',
    )
    image = models.ImageField(
        verbose_name='Картинка рецепта',
        help_text='Добавьте изображение рецепта',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True)

    class Meta:
        ordering = ['-id']
        default_related_name = 'recipe'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipe')]


class IngredientRecipe(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        verbose_name='Название рецепта',
        on_delete=models.CASCADE,
        help_text='Выберите рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        help_text='Укажите ингредиенты')
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальное количество ингредиентов 1')],
        verbose_name='Количество',
        help_text='Укажите количество ингредиента')

    class Meta:
        verbose_name = 'Cостав рецепта'
        verbose_name_plural = 'Состав рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients')]

    def __str__(self):
        return f'{self.ingredient} {self.amount}'


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'ShoppingCartObj {self.user} - {self.recipe}'


class Favorite(models.Model):

    user = models.ForeignKey(
        User,
        related_name='favorite',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'Favorite Obj {self.user} - {self.recipe}'
