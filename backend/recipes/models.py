from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from users.models import MyUser

MAX_CHARFIELD_LENGHT = 150
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000
MIN_INGREDIENT_AMONG = 1
MAX_INGREDIENT_AMONG = 32000


class Ingredient(models.Model):

    name = models.CharField(
        db_index=True,
        max_length=MAX_CHARFIELD_LENGHT,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=MAX_CHARFIELD_LENGHT,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Tag(models.Model):

    name = models.CharField(
        'Название тега', max_length=MAX_CHARFIELD_LENGHT, unique=True,)
    slug = models.SlugField(
        'Слаг тега', max_length=MAX_CHARFIELD_LENGHT, unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Recipe(models.Model):

    author = models.ForeignKey(
        MyUser,
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
        verbose_name='Тег',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Опишите приготовление рецепта'
    )
    name = models.CharField(
        max_length=MAX_CHARFIELD_LENGHT,
        db_index=True,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                'Минимальное время приготовления 1'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                'Максимальное время приготовления 32000'
            )
        ],
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

    def author_info(self):
        return f'{self.author.first_name} {self.author.last_name}'

    def tags_names(self):
        return ', '.join(tag.name for tag in self.tags.all())

    class Meta:
        ordering = ['-id']
        default_related_name = 'recipe'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipe')]

    def __str__(self):
        return self.name


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
            MinValueValidator(
                MIN_INGREDIENT_AMONG,
                'Минимальное колличество ингредиента 1'
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMONG,
                'Максимальное колличетсво ингредиентов'
            ),
        ],
        verbose_name='Количество',
        help_text='Укажите количество ингредиента'
    )

    class Meta:
        verbose_name = 'Cостав рецепта'
        verbose_name_plural = 'Составы рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients')]
        ordering = ['-id']

    def __str__(self):
        return f'{self.ingredient} {self.amount}'


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        MyUser,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепт в корзине',
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ['-id']

    def __str__(self):
        return f'Покупка {self.user} - {self.recipe}'


class Favorite(models.Model):

    user = models.ForeignKey(
        MyUser,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Рецепт в избранном'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['-id']

    def __str__(self):
        return f'{self.user} избравший {self.recipe}'
