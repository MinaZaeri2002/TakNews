from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.zoomit_spider import ZoomitSpider


class Command(BaseCommand):
    help = 'Runs the Zoomit spider ...'

    def handle(self, *args, **options):
        import os
        import django

        os.environ.setdefault('DJANGO_SETTINGS_MODULE','TakNews.settings')
        django.setup()

        process = CrawlerProcess(get_project_settings())
        process.crawl(ZoomitSpider)
        process.start()

        self.stdout.write('Done')
