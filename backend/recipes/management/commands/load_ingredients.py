import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from CSV file'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(
            settings.BASE_DIR.parent, 'data', 'ingredients.csv'
        )

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        ingredients = []

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for name, measurement_unit in reader:
                ingredients.append(
                    Ingredient(
                        name=name,
                        measurement_unit=measurement_unit
                    )
                )

        Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded ingredients')
        )
