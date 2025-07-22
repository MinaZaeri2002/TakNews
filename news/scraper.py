from billiard import Process
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.zoomit_spider import ZoomitSpider


def run_spider():
    process = CrawlerProcess(get_project_settings())
    process.crawl(ZoomitSpider)
    process.start()


def scrape_news():
    p = Process(target=run_spider)
    p.start()
    p.join()

    if p.exitcode == 0:
        print("Scraping completed successfully")
    else:
        print(f"Scraping failed with exit code: {p.exitcode}")