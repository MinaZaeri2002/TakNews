from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import News
from .serializers import NewsSerializer
from .filters import NewsFilter


class NewsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NewsAPIView(APIView):
    pagination_class = NewsPagination

    def get(self, request, pk=None, format=None):
        if pk:
            try:
                news_item = News.objects.get(pk=pk, is_active=True)
                serializer = NewsSerializer(news_item)
                return Response(serializer.data)
            except News.DoesNotExist:
                return Response({'error': 'News not found'}, status=status.HTTP_404_NOT_FOUND)

        queryset = News.objects.filter(is_active=True).order_by('-published_at')

        filtered_queryset = NewsFilter(request.GET, queryset=queryset).qs

        search_query = request.GET.get('search')
        if search_query:
            filtered_queryset = filtered_queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        ordering = request.GET.get('ordering')
        allowed_ordering_fields = ['published_at', '-published_at', 'title', '-title']
        if ordering in allowed_ordering_fields:
            filtered_queryset = filtered_queryset.order_by(ordering)
        else:
            filtered_queryset = filtered_queryset.order_by('-published_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(filtered_queryset, request)

        if page is not None:
            serializer = NewsSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = NewsSerializer(filtered_queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = NewsSerializer(data=request.data)
        if serializer.is_valid():
            news = serializer.save()
            return Response(NewsSerializer(news).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


