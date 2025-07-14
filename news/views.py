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

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(filtered_queryset, request)

        if page is not None:
            serializer = NewsSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = NewsSerializer(filtered_queryset, many=True)
        return Response(serializer.data)


