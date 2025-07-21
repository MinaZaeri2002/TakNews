import re
from urllib.parse import urljoin
import jdatetime
import scrapy
from news.models import News


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

    first_db_url = None

    def __init__(self, *args, **kwargs):
        super(ZoomitSpider, self).__init__(*args, **kwargs)
        last_news = News.objects.order_by('-published_at').first()
        self.last_db_url = last_news.source if last_news else None
        self.found_last_db_url = False
        self.current_page = 1
        self.max_pages = 10

    def start_requests(self):
        if self.last_db_url is None:
            for page in range(1, self.max_pages + 1):
                url = f"https://www.zoomit.ir/archive/?pageNumber={page}"
                yield scrapy.Request(
                    url,
                    callback=self.parse_archive,
                    meta={"playwright": True, "page_number": page}
                )

        else:
            url = f"https://www.zoomit.ir/archive/?pageNumber={self.current_page}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_archive,
                meta={'playwright': True, 'page_number': self.current_page},
                dont_filter=True
            )

    def parse_archive(self, response):
        page_number = response.meta["page_number"]
        self.logger.info(f"Archive page {page_number}: {response.url}")

        for href in response.css("a::attr(href)").getall():
            if not href:
                continue
            href = self.clean_url(response.url, href)

            if href == self.last_db_url:
                self.logger.info(f"Reached last_db_url: {href}. Stopping...")
                self.found_last_db_url = True
                return

            elif self.article_pattern.match(href):
                yield scrapy.Request(
                    href,
                    callback=self.parse_news
                )

        if not self.found_last_db_url and self.current_page < self.max_pages:
            self.current_page += 1
            next_url = f"https://www.zoomit.ir/archive/?pageNumber={self.current_page}"
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_archive,
                meta={'playwright': True, 'page_number': self.current_page},
                dont_filter=True
            )

    def parse_news(self, response):
        title = response.css('h1::text').get()
        content = self.get_content(response)

        yield {
            'title': title,
            'content': content,
            'source': response.url,
            'published_at': self.get_date_time(response),
            'is_active': True,
            'tags': response.xpath('//*[@id="__next"]/div[2]/div[1]/main/article/header/div/div/div[2]/div[1]/a/span//text()').getall(),
        }

    def clean_url(self, base, href):
        if href.startswith("/"):
            href = urljoin(base, href)
        return href.split("#")[0].strip()

    def get_content(self, response):
        texts = response.xpath('//*[@id="__next"]/div[2]/div[1]/main/article/div/div[3]/div/div//text() | //*[@id="__next"]/div[2]/div[1]/main/article/div/div[5]/div/div/div//text()').getall()
        return '\n'.join(t.strip().replace('\u200c', '') for t in texts if t.strip())

    def get_date_time(self, response):
        raw = response.xpath('//*[@id="__next"]/div[2]/div[1]/main/article/header/div/div/div[2]/span[1]//text()').get()
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
