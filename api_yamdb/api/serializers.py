import re

from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from reviews.constants import (
    FORBIDDEN_USERNAME,
    MAX_CONFIRMATION_CODE,
    MAX_EMAIL_LENGTH,
    MAX_SCORE,
    MAX_USERNAME_LENGTH,
    MIN_SCORE,
    SCORE_ERROR,
    USERNAME_REGEX,
)
from reviews.models import Category, Comment, Genre, Review, Title, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description', 'genre', 'category', 'rating'
        )


class TitleWriteSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Genre.objects.all(),
        allow_empty=False
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')

    def to_representation(self, instance):
        return TitleReadSerializer(instance, context=self.context).data


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    score = serializers.IntegerField()

    class Meta:
        model = Review
        fields = ('id', 'text', 'score', 'author', 'pub_date')

    def validate_score(self, value):
        if not (MIN_SCORE <= value <= MAX_SCORE):
            raise serializers.ValidationError(
                SCORE_ERROR.format(min=MIN_SCORE, max=MAX_SCORE)
            )
        return value

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        title = self.context.get('view').kwargs.get('title_id')

        if request.method == 'POST':
            if Review.objects.filter(title_id=title, author=user).exists():
                raise serializers.ValidationError(
                    {'detail': 'Вы уже оставляли отзыв на это произведение.'}
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=MAX_EMAIL_LENGTH)
    username = serializers.CharField(max_length=MAX_USERNAME_LENGTH)

    def validate_username(self, value):
        if value == FORBIDDEN_USERNAME:
            raise serializers.ValidationError('Этот никнейм запрещён')
        if not re.match(USERNAME_REGEX, value):
            raise serializers.ValidationError(
                'Никнейм может содержать только буквы, '
                'цифры и @/./+/-/_ символы.'
            )
        return value

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        if User.objects.filter(username=username, email=email).exists():
            return data
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует.'
            )
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return data

    def create(self, validated_data):
        user, _ = User.objects.get_or_create(**validated_data)
        return user


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=MAX_USERNAME_LENGTH)
    confirmation_code = serializers.CharField(
        max_length=MAX_CONFIRMATION_CODE)

    def validate(self, data):
        user = get_object_or_404(User, username=data.get('username'))
        code = data.get('confirmation_code')
        if not default_token_generator.check_token(user, code):
            raise serializers.ValidationError('Не верный код подтверждения')
        return {'access': str(AccessToken.for_user(user))}
