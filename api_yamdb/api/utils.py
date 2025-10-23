from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail


def get_confirmation_code(user):
    return default_token_generator.make_token(user)


def send_confirmation_code(user):
    user.confirmation_code = get_confirmation_code(user)
    user.save()
    send_mail(
        'Данные для получения токена',
        f'Код подтверждения {user.confirmation_code}',
        settings.EMAIL_FROM_ADDRESS,
        [user.email],
    )
