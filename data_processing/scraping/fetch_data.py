import asyncio
import json
from datetime import datetime
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from dotenv import load_dotenv

from sitemap_collector import SitemapCollector

# ==================== Load configurations ====================
MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(MODULE_DIR / ".env")
with open(MODULE_DIR / "config.yaml") as f:
    _cfg = yaml.safe_load(f)

# ==================== Configure ====================
DATA_ROOT_DIR = REPO_ROOT / "data"
DATA_RAW_DIR = DATA_ROOT_DIR / "raw"  # input:  data/raw/<year>/<issue>/<doc>.json

DOCUMENT_LIMIT = int(_cfg["document_limit"]) if _cfg["document_limit"] else -1  # If there is no limit defined, take all
TIMEOUT = int(_cfg["timeout"]) if _cfg["timeout"] else 10_000  # Playwright timeout in milliseconds (default 10s); set to 0 for no timeout
MAX_REQUESTS_PER_CRAWL = int(_cfg["max_requests_per_crawl"]) if _cfg["max_requests_per_crawl"] else 1000

start = datetime.now()
print("Collecting URLs from the sitemap...")
sc = SitemapCollector("https://narodne-novine.nn.hr/sitemap.xml")
print(f"Collected {len(sc.all_urls)} URLs from the sitemap.")
print("Time taken to collect URLs:", datetime.now() - start)

async def main() -> None:
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=MAX_REQUESTS_PER_CRAWL,
        headless=True,  # Run in headless mode (set to False to see the browser).
        browser_type='firefox',  # Use Firefox browser.
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        # Follow any redirects and wait for the final page to fully load.
        await context.page.wait_for_load_state("networkidle", timeout=TIMEOUT)

        content = await context.page.content()
        soup = BeautifulSoup(content, "html.parser")

        tbody = soup.select_one("#article-details-scroll > table.detailsTable > tbody")
        if tbody is None:
            print("Could not find the details table on the page.", context.request.url)
            return

        def find_td(label):
            """Return the first td whose text contains label, or None."""
            for row in tbody.select("tr"):
                td = row.select_one("td")
                if td and label in td.get_text():
                    return td
            return None

        def get_field(label):
            td = find_td(label)
            if not td:
                return None
            return td.get_text(strip=True).replace(label, "").strip()

        def get_link(label):
            td = find_td(label)
            if not td:
                return None, None
            a = td.select_one("a")
            if a:
                return a.get_text(strip=True), a["href"]
            # No <a> — plain text value (older articles); strip label and &nbsp;
            text = td.get_text(strip=True).replace(label, "").replace("\xa0", " ").strip()
            return text or None, None

        izdanje_text, izdanje_url = get_link("Izdanje:")
        eli_text, eli_url         = get_link("ELI:")

        data = {
            "dio":           get_field("Dio NN:"),
            "vrsta":         get_field("Vrsta dokumenta:"),
            "izdanje":       izdanje_text,
            "izdanjeUrl":    izdanje_url,
            "brojDokumenta": get_field("Broj dokumenta u izdanju:"),
            "stranica":      get_field("Stranica tiskanog izdanja:"),  # None when absent
            "donositelj":    get_field("Donositelj:"),
            "datum":         get_field("Datum tiskanog izdanja:"),
            "eli":           eli_text,
            "eliUrl":        eli_url,
            "naslov":        soup.select_one("#sticky > h2").get_text(strip=True),
            "doc":           str(doc_el) if (doc_el := soup.select_one("#html-content-frame > div.sl-content > div.doc > div.article-column")) else None,
        }

        if not eli_text and not eli_url:
            print("No ELI info found, skipping save.", context.request.url)
            return

        path = eli_text.replace("/eli/sluzbeni/", "") if eli_text else eli_url.replace("https://narodne-novine.nn.hr/eli/sluzbeni/", "")
        filename = path.split("/")[-1] + ".json"
        folder_name = DATA_RAW_DIR / Path(*path.split("/")[:-1])

        folder_name.mkdir(parents=True, exist_ok=True)

        # Parse content and extract data
        with open(folder_name / filename, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False))

    # Filter out URLs that have already been fetched (file exists in data/raw).
    def is_cached(url: str) -> bool:
        path = url.replace("https://narodne-novine.nn.hr/eli/sluzbeni/", "")
        filename = path.split("/")[-1] + ".json"
        folder_name = DATA_RAW_DIR / Path(*path.split("/")[:-1])
        return (folder_name / filename).exists()

    document_limit = DOCUMENT_LIMIT if 0 < DOCUMENT_LIMIT < len(sc.all_urls) else len(sc.all_urls)
    urls_to_fetch = [url for url in sc.all_urls[0:document_limit] if not is_cached(url)]

    # Run the crawler with the initial list of URLs.
    await crawler.run(urls_to_fetch)


if __name__ == '__main__':
    print("Starting the crawler...")
    start = datetime.now()
    asyncio.run(main())
    print("Crawling completed in:", datetime.now() - start)
