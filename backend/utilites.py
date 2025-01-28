import csv
import os

import django


def load_ingredients_from_csv_bulk(csv_filepath):
    ingredients = []

    with open(csv_filepath, mode='r') as file:
        reader = csv.reader(file)

        for row in reader:
            name, measurement_unit = row
            ingredients.append(Ingredient(
                name=name,
                measurement_unit=measurement_unit
            )
            )

    Ingredient.objects.bulk_create(ingredients)


if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
    django.setup()
    from recipes.models import Ingredient
    csv_filepath = 'ingredients.csv'
    load_ingredients_from_csv_bulk(csv_filepath)
