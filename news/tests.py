from rest_framework.test import APIClient
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from datetime import timedelta, datetime
from .models import News, Tag, Source


class NewsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.source1 = Source.objects.create(name='test1', website='https://test1.com')
        self.source2 = Source.objects.create(name='test2', website='https://test2.com')

        self.tag_tech = Tag.objects.create(name='technology', slug='technology')
        self.tag_economy = Tag.objects.create(name='economy', slug='economy')
        self.tag_sport = Tag.objects.create(name='sport', slug='sport')

        self.news1 = News.objects.create(
            title="technology news",
            content="This is a news about technology. Artificial intelligence is transforming industries worldwide.",
            source=self.source1,
            external_url='https://test.com/news1',
            published_at=timezone.now() - timedelta(days=2),
            is_active=True
        )
        self.news1.tags.add(self.tag_tech)

        self.news2 = News.objects.create(
            title="economy news",
            content="This is a news about economy. Stock markets show significant growth this quarter.",
            source=self.source2,
            external_url='https://test.com/news2',
            published_at=timezone.now() - timedelta(days=1),
            is_active=True
        )
        self.news2.tags.add(self.tag_economy)

        self.news3 = News.objects.create(
            title="sport news",
            content="This is a news about sport.",
            source=self.source1,
            external_url='https://test.com/news3',
            published_at=timezone.now(),
            is_active=True
        )
        self.news3.tags.add(self.tag_sport)

        self.news4 = News.objects.create(
            title="technology2 news",
            content="This is a news about technology2. Quantum computing breakthrough achieved.",
            source=self.source1,
            external_url='https://test.com/news4',
            published_at=timezone.now() - timedelta(days=3),
            is_active=True
        )
        self.news4.tags.add(self.tag_tech)

        self.inactive_news = News.objects.create(
            title="inactive news",
            content="This is a news about inactive news.",
            source=self.source1,
            external_url='https://test.com/inactive',
            published_at=timezone.now(),
            is_active=False
        )

    def test_get_news_list(self):
        url = '/api/news/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)

        results = response.data['results']
        self.assertEqual(len(results), 4)

        self.assertEqual(results[0]['title'], 'sport news')
        self.assertEqual(results[1]['title'], 'economy news')
        self.assertEqual(results[2]['title'], 'technology news')
        self.assertEqual(results[3]['title'], 'technology2 news')

        first_item = results[0]
        self.assertIn('id', first_item)
        self.assertIn('title', first_item)
        self.assertIn('content', first_item)
        self.assertIn('source', first_item)
        self.assertIn('tags', first_item)
        self.assertIn('external_url', first_item)
        self.assertIn('published_at', first_item)

    def test_get_single_news(self):
        url = f'/api/news/{self.news1.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'technology news')
        self.assertEqual(response.data['content'], 'This is a news about technology. Artificial intelligence is transforming industries worldwide.')

        tags = [tag['name'] for tag in response.data['tags']]
        self.assertEqual(tags, ['technology'])

    def test_news_not_found(self):
        url = f'/api/news/9999/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'News not found')

    def test_filter_by_tag(self):
        url = '/api/news/'
        response = self.client.get(url, {'tags': 'technology'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 2)
        titles = [item['title'] for item in results]
        self.assertIn('technology news', titles)
        self.assertIn('technology2 news', titles)
        self.assertNotIn('sport news', titles)

    def test_include_keyword_filter(self):
        url = '/api/news/'
        response = self.client.get(url, {'keyword_include': 'Football sport'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'sport news')

    def test_exclude_keyword_filter(self):
        url = '/api/news/'
        response = self.client.get(url, {'keyword_exclude': 'sport'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        titles = [item['title'] for item in results]
        self.assertIn('technology news', titles)
        self.assertIn('technology2 news', titles)
        self.assertIn('economy news', titles)
        self.assertNotIn('sport news', titles)

    def test_combined_filters(self):
        url = '/api/news/'
        params = {
            'tags': 'technology',
            'keyword_include': 'technology',
            'keyword_exclude': 'Quantum',
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'technology news')

    def test_pagination(self):
        for i in range(106):
            News.objects.create(
                title=f"Extra News {i}",
                content="Additional content",
                source=self.source1,
                published_at=timezone.now(),
                is_active=True
            )

        response = self.client.get('/api/news/')
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['count'], 110)

        response = self.client.get('/api/news/', {'page_size': 5})
        self.assertEqual(len(response.data['results']), 5)

        response = self.client.get('/api/news/', {'page_size': 150})
        self.assertEqual(len(response.data['results']), 100)

        response = self.client.get('/api/news/', {'page': 6})
        self.assertEqual(len(response.data['results']), 10)

    def test_inactive_news_not_returned(self):
        url = f'/api/news/{self.inactive_news.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get('/api/news/')
        news_ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(self.inactive_news.id, news_ids)

    def test_case_insensitive_filter(self):
        response = self.client.get('/api/news/', {'tags': 'TECHNOLOGY'})
        self.assertEqual(len(response.data['results']), 2)

        response = self.client.get('/api/news/', {'keyword_include': 'ARTIFICIAL'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'technology news')

    def test_published_at_format(self):
        url = f'/api/news/{self.news1.id}/'
        response = self.client.get(url)
        self.assertIsInstance(response.data['published_at'], str)

        datetime.fromisoformat(response.data['published_at'])


