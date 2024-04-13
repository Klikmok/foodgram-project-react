import csv
import os

from api.models import Ingredient
from django.core.management.base import BaseCommand
from progress.bar import IncrementalBar

from backend import settings


def ingredient_create(row):
    Ingredient.objects.get_or_create(
        name=row[0],
        measurement_unit=row[1]
    )


class Command(BaseCommand):
    help = "Load data to DB"

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'data/ingredients.csv')
        with open(path, 'r', encoding='utf-8') as file:
            count = sum(1 for row in file)
        with open(path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            custom_bar = IncrementalBar('ingredients.csv'.ljust(17), max=count)
            next(reader)
            for row in reader:
                custom_bar.next()
                ingredient_create(row)
            custom_bar.finish()
        self.stdout.write("Data has been loaded succesfully.")
