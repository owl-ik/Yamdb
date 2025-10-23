from django_filters.rest_framework import FilterSet, filters

from reviews.models import Title


class TitleFilter(FilterSet):
    genre = filters.CharFilter(field_name='genre__slug')
    category = filters.CharFilter(field_name='category__slug')
    name = filters.CharFilter(field_name='name')

    class Meta:
        model = Title
        fields = ('genre', 'category', 'name', 'year')
