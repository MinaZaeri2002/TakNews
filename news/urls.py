from django.urls import path, include
from .views import NewsAPIView

urlpatterns = [
    path('news/', NewsAPIView.as_view(), name='news-lisr'),
    path('news/<int:pk>/', NewsAPIView.as_view(), name='news-detail'),
]