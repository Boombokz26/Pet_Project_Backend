import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from fitness.models import Exercise


class Command(BaseCommand):
    help = "Import exercises from CSV"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(
            settings.BASE_DIR,
            "DataSets",
            "stretch_exercise_dataset new.csv"
        )

        with open(file_path, newline='', encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                Exercise.objects.create(
                    name=row.get("exercise_name"),
                    description=row.get("description", ""),
                    difficulty_level=row.get("difficulty", "Beginner"),
                )

        self.stdout.write(self.style.SUCCESS("Import completed successfully"))