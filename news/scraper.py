from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.zoomit_spider import ZoomitSpider


def scrape_news():
    process = CrawlerProcess(get_project_settings())
    process.crawl(ZoomitSpider)
    process.start()