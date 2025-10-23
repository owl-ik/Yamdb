from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from rest_framework.exceptions import ValidationError

from reviews.constants import (
    MAX_EMAIL_LENGTH,
    MAX_CATEGORY_AND_GENRE_LENGTH,
    MAX_SCORE,
    MAX_USERNAME_LENGTH,
    MIN_SCORE,
    SCORE_ERROR,
    USERNAME_REGEX,
)
from reviews.validators import validate_username_not_me, validate_year

username_validator = RegexValidator(
    regex=USERNAME_REGEX,
    message=' Принимаются только эти символы : @ . + - _'
)


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    ]

    MAX_ROLE_LENGTH = max(len(choice[0]) for choice in ROLE_CHOICES)

    bio = models.TextField(
        blank=True,
        verbose_name='Биография'
    )
    role = models.CharField(
        max_length=MAX_ROLE_LENGTH,
        choices=ROLE_CHOICES,
        default=USER,
        verbose_name='Роль'
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name='Электронная почта'
    )
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        validators=[username_validator, validate_username_not_me],
        verbose_name='Имя пользователя'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR


class BaseCategoryGenreModel(models.Model):
    name = models.CharField(max_length=MAX_CATEGORY_AND_GENRE_LENGTH,
                            verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(BaseCategoryGenreModel):
    class Meta(BaseCategoryGenreModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(BaseCategoryGenreModel):
    class Meta(BaseCategoryGenreModel.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    name = models.CharField(
        max_length=MAX_CATEGORY_AND_GENRE_LENGTH,
        verbose_name='Название произведения'
    )
    year = models.SmallIntegerField(
        verbose_name='Год выпуска',
        validators=[validate_year]
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
        verbose_name='Жанр'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='titles',
        null=True,
        verbose_name='Категория'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class PubAuthorModel(models.Model):
    """Абстрактная модель с общими полями для Review и Comment"""
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        abstract = True
        ordering = ['-pub_date']
        default_related_name = '%(class)ss'

    def __str__(self):
        return f'{self._meta.verbose_name} от {self.author.username}'


class Review(PubAuthorModel):
    title = models.ForeignKey(
        'Title',
        on_delete=models.CASCADE,
        verbose_name='Произведение',
    )
    score = models.PositiveSmallIntegerField(verbose_name='Оценка')

    class Meta(PubAuthorModel.Meta):
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review_per_author',
            ),
        ]

    def __str__(self):
        return f'Отзыв на {self.title} от {self.author.username}'

    def clean(self):
        if not (MIN_SCORE <= self.score <= MAX_SCORE):
            raise ValidationError(
                SCORE_ERROR.format(min=MIN_SCORE, max=MAX_SCORE)
            )


class Comment(PubAuthorModel):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name='Отзыв',
    )

    class Meta(PubAuthorModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return ('Комментарий к отзыву'
                f' {self.review.id} от {self.author.username}')
