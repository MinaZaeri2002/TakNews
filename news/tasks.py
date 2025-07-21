from celery import shared_task
from news.scraper import scrape_news


@shared_task
def scrape_news_task():
    print("Starting news scraping task...")
    scrape_news()
    print("News scraping completed!")
