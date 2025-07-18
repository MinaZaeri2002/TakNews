import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urlparse
import jdatetime


class ZoomitSpider(CrawlSpider):
    name = 'zoomit'
    allowed_domains = ['zoomit.ir']
    start_urls = [
        'https://www.zoomit.ir/mobile/',
        'https://www.zoomit.ir/tablet/',
        'https://www.zoomit.ir/laptop/',
        'https://www.zoomit.ir/tv/',
        'https://www.zoomit.ir/wearables/',
        'https://www.zoomit.ir/hardware/',
        'https://www.zoomit.ir/software-application/',
        'https://www.zoomit.ir/os/',
        'https://www.zoomit.ir/internet-network/',
        'https://www.zoomit.ir/gaming/',
        'https://www.zoomit.ir/cryptocurrency/',
        'https://www.zoomit.ir/shutter/',
        'https://www.zoomit.ir/tech-iran/',
        'https://www.zoomit.ir/review/',
        'https://www.zoomit.ir/featured-articles/',
        'https://www.zoomit.ir/scientific/',
        'https://www.zoomit.ir/fundamental-science/',
        'https://www.zoomit.ir/space/',
        'https://www.zoomit.ir/health-medical/',
        'https://www.zoomit.ir/energy-environment/',
        'https://www.zoomit.ir/buying-guide/',
        'https://www.zoomit.ir/car/',
        'https://www.zoomit.ir/mobile-learning/',
        'https://www.zoomit.ir/howto/',
        'https://www.zoomit.ir/photography-learning/',
    ]

    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.DjangoNewsPipeline': 300
        },
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'logs/zoomit_scraping.log',
    }

    def __init__(self, *args, **kwargs):
        self.allowed_paths = [urlparse(url).path for url in self.start_urls]

        allow_pattern = r'(' + '|'.join(re.escape(path) for path in self.allowed_paths) + r')[^\s]*\d+'

        self.rules = (
            Rule(LinkExtractor(
                restrict_css='article a, .article-card a, .news-item a',
                allow=[allow_pattern],
                deny=[
                    r'/search/',
                    r'/profile/',
                    r'/video/',
                    r'/about-us/',
                    r'/advertisement/',
                    r'/hire/',
                    r'/contact-us/',
                    r'/community-guidelines/',


                ]
            ),
                callback='parse_news',
                follow=True,
            ),
        )

        super().__init__(*args, **kwargs)

    def parse_news(self, response):
        item = {
            'title': response.css('h1::text').get(),
            'content': self.get_content(response),
            'source': response.url,
            'published_at': self.get_date_time(response),
            'is_active': True,
            'tags': response.css('div.sc-a11b1542-0.fCUOzW a span::text').getall(),
        }

        yield item

    def get_content(self, response):
        content_parts = []
        for t in response.css('div.sc-481293f7-1.jrhnOU *::text').getall():
            cleaned = t.strip().replace('\u200c', '')
            if cleaned:
                content_parts.append(cleaned)
        return '\n'.join(content_parts)

    def get_date_time(self, response):
        raw = response.css('span[class*="fa"]::text').get().strip()

        if not raw:
            self.logger.warning('No date found')
            return None

        parts = [p.strip() for p in raw.split(' - ')]
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else '00:00'

        if len(date_part.split()) == 4:
            _, day_str, month_fa, year_str = date_part.split()
        elif len(date_part.split()) == 3:
            day_str, month_fa, year_str = date_part.split()
        else:
            raise ValueError(f"Unexpected date format: {date_part}")

        day = int(day_str)
        year = int(year_str)

        month_map = {
            'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3,
            'تیر': 4, 'مرداد': 5, 'شهریور': 6,
            'مهر': 7, 'آبان': 8, 'آذر': 9,
            'دی': 10, 'بهمن': 11, 'اسفند': 12,
        }

        month = month_map.get(month_fa)

        hour, minute = map(int, time_part.split(':'))

        jalali_dt = jdatetime.datetime(year, month, day, hour, minute)

        date_time_field = jalali_dt.togregorian()

        return date_time_field




