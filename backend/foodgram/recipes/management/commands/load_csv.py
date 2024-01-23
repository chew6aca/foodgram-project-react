import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import data from CSV files into the database'

    def handle_ingredients(self, *args, **kwargs):
        with open('ingredients.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            objs = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                ) for item in reader
            ]
            Ingredient.objects.bulk_create(objs)

    def handle(self, *args, **kwargs):
        self.handle_ingredients()
