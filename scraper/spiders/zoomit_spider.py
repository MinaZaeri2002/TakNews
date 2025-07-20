import re
from urllib.parse import urljoin
import jdatetime
import scrapy


class ZoomitSpider(scrapy.Spider):
    name = 'zoomit'
    allowed_domains = ['zoomit.ir']
    start_urls = ['https://www.zoomit.ir/archive/']

    custom_settings = {
        'ITEM_PIPELINES': {
            'scraper.pipelines.DjangoNewsPipeline': 300
        },
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'logs/zoomit_scraping.log',
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }

    article_pattern = re.compile(r'^https?://(?:www\.)?zoomit\.ir/[^/]+/\d{5,}-[a-z0-9-]+/?$')

    def start_requests(self):
        for page in range(1, 10):
            url = f"https://www.zoomit.ir/archive/?pageNumber={page}"
            yield scrapy.Request(
                url,
                callback=self.parse_archive,
                meta={"playwright": True, "page_number": page}
            )

    def parse_archive(self, response):
        page_number = response.meta["page_number"]
        self.logger.info(f"Archive page {page_number}: {response.url}")

        for href in response.css("a::attr(href)").getall():
            if not href:
                continue
            href = self.clean_url(response.url, href)
            if self.article_pattern.match(href):
                yield scrapy.Request(
                    href,
                    callback=self.parse_news
                )

    def parse_news(self, response):
        yield {
            'title': response.css('h1::text').get(),
            'content': self.get_content(response),
            'source': response.url,
            'published_at': self.get_date_time(response),
            'is_active': True,
            'tags': response.css('div.sc-a11b1542-0.fCUOzW a span::text').getall(),
        }

    def clean_url(self, base, href):
        if href.startswith("/"):
            href = urljoin(base, href)
        return href.split("#")[0].strip()

    def get_content(self, response):
        texts = response.css('div.sc-481293f7-1.jrhnOU *::text').getall()
        return '\n'.join(t.strip().replace('\u200c', '') for t in texts if t.strip())

    def get_date_time(self, response):
        raw = response.css('span[class*="fa"]::text').get()
        if not raw:
            return None

        raw = raw.strip()
        parts = [p.strip() for p in raw.split(' - ')]
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else '00:00'

        tokens = date_part.split()
        if len(tokens) == 4:
            _, day_str, month_fa, year_str = tokens
        elif len(tokens) == 3:
            day_str, month_fa, year_str = tokens
        else:
            return None

        day = int(day_str)
        year = int(year_str)
        month_map = {
            'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3,
            'تیر': 4, 'مرداد': 5, 'شهریور': 6,
            'مهر': 7, 'آبان': 8, 'آذر': 9,
            'دی': 10, 'بهمن': 11, 'اسفند': 12,
        }
        month = month_map.get(month_fa)
        if not month:
            return None

        hour, minute = map(int, time_part.split(':'))
        jalali_dt = jdatetime.datetime(year, month, day, hour, minute)
        return jalali_dt.togregorian()
