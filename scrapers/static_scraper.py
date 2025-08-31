from __future__ import annotations
import requests
from .base_scraper import BaseScraper, ScrapeResult

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36 SupplierMonitorBot/1.0"
}

class StaticScraper(BaseScraper):
    def fetch(self, url: str) -> ScrapeResult:
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            return ScrapeResult(ok=r.ok, status_code=r.status_code, html=r.text if r.ok else r.text, url=url)
        except Exception as e:
            return ScrapeResult(ok=False, status_code=None, html=None, url=url, error=str(e))
