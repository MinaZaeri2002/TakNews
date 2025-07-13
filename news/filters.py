import django_filters
from django.db.models import Q
from .models import News, Tag, Source


class NewsFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method='filter_by_tag')
    keyword_include = django_filters.CharFilter(method='filter_include_keyword')
    keyword_exclude = django_filters.CharFilter(method='filter_exclude_keyword')

    class Meta:
        model = News
        fields = []

    def filter_by_tag(self, queryset, name, value):
        tag = value.split(',')
        return queryset.filter(tag__name__in=tag)

    def filter_include_keyword(self, queryset, name, value):
        keywords = value.split()
        query = Q()
        for keyword in keywords:
            query |= Q(title__icontains=keyword) | Q(content__icontains=keyword)
        return queryset.filter(query)

    def filter_exclude_keyword(self, queryset, name, value):
        keywords = value.split()
        query = Q()
        for keyword in keywords:
            query |= Q(title__icontains=keyword) | Q(content__icontains=keyword)
        return queryset.exclude(query)

