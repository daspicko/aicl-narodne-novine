import os
import json
import xml.etree.ElementTree as ET
import asyncio

from crawlee.crawlers import HttpCrawler, HttpCrawlingContext
from crawlee.http_clients import HttpxHttpClient

class SitemapCollector:

    SITEMAP_OUTPUT_FILENAME = "all_urls.json"

    def __init__(self, sitemap_url="https://narodne-novine.nn.hr/sitemap.xml", requests_per_crawl=None):
        self.sitemap_url = sitemap_url
        self.requests_per_crawl = requests_per_crawl
        self.all_urls = []

        if os.path.exists(SitemapCollector.SITEMAP_OUTPUT_FILENAME):
            with open(SitemapCollector.SITEMAP_OUTPUT_FILENAME, "r") as f:
                self.all_urls = json.load(f)
            return  # Early exit

        # Fetch data from Web
        asyncio.run(self.start_crawler())

    async def start_crawler(self):
        # HttpCrawler fetches raw HTTP responses - no browser needed for plain XML.
        self.crawler = HttpCrawler(
            max_requests_per_crawl=self.requests_per_crawl,
            http_client=HttpxHttpClient(),
        )

        @self.crawler.router.default_handler
        async def request_handler(context: HttpCrawlingContext) -> None:
            xml_content = (await context.http_response.read()).decode('utf-8')

            if "<sitemapindex" in xml_content:
                items = self.extract_items(xml_content, "loc")
                filtered_items = [i for i in items if i.startswith("https://narodne-novine.nn.hr/sitemap_") and i.endswith(".xml")]
                #self.all_urls.extend(filtered_items)

                # Enqueue discovered sub-sitemap URLs.
                await context.add_requests(filtered_items)
            else:
                items = self.extract_items(xml_content, "loc")
                filtered_items = [i for i in items if i.startswith("https://narodne-novine.nn.hr/clanci/sluzbeni/") and i.endswith(".html")]
                self.all_urls.extend(filtered_items)

        # Run the crawler with the initial URL.
        await self.crawler.run([self.sitemap_url])

        self.crawler.log.info(f'Extracted data count: {len(self.all_urls)}')

        # Save results to cache file for future runs.
        with open(SitemapCollector.SITEMAP_OUTPUT_FILENAME, "w") as f:
            json.dump(self.all_urls, f)

    @staticmethod
    def extract_items(xml_content, item_name):
        sanitized_text = xml_content.strip()
        root = ET.ElementTree(ET.fromstring(sanitized_text)).getroot()

        items = []
        for element in root:
            for i in element:
                if i.tag.endswith(item_name):
                    items.append(i.text)
        return items

if __name__ == "__main__":
    sitemap_collector = SitemapCollector()
