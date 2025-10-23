from django.utils import timezone
from rest_framework.exceptions import ValidationError

from reviews.constants import FORBIDDEN_USERNAME


def validate_username_not_me(value):
    if value == FORBIDDEN_USERNAME:
        raise ValidationError('Этот никнейм запрещён')


def validate_year(value):
    current_year = timezone.now().year
    if value > current_year:
        raise ValidationError(
            f'Год выпуска не может быть больше {current_year}.')
