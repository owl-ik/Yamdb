import os
import csv

from django.apps import apps
from django.db.models import ForeignKey
from django.core.management.base import BaseCommand

DATA_DIR = 'static/data'

MODEL_CSV = [
    ('Category', 'category.csv'),
    ('Genre', 'genre.csv'),
    ('User', 'users.csv'),
    ('Title', 'titles.csv'),
    ('Review', 'review.csv'),
    ('Comment', 'comments.csv'),
]


def resolve_foreign_keys(model, row):
    for field in model._meta.get_fields():
        if isinstance(field, ForeignKey):
            field_name = field.name
            if field_name in row and row[field_name]:
                related_model = field.remote_field.model
                obj = related_model.objects.get(id=row[field_name])
                row[field_name] = obj
    return row


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true')

    def handle(self, *args, **options):
        clear = options['clear']
        for model_name, filename in MODEL_CSV:
            model = self.get_model(model_name)
            path = os.path.join(DATA_DIR, filename)
            if clear:
                model.objects.all().delete()
                self.stdout.write(self.style.NOTICE(
                    f'Очищена модель {model_name}'))
            objects_to_create = []
            with open(path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row = resolve_foreign_keys(model, row)
                    obj = model(**row)
                    objects_to_create.append(obj)
            model.objects.bulk_create(objects_to_create)
            self.stdout.write(self.style.SUCCESS(
                f'Импортировано: {model_name}'))

    def get_model(self, model_name):
        for app_label in ('reviews', 'api'):
            try:
                return apps.get_model(app_label, model_name)
            except LookupError:
                continue
        return None
