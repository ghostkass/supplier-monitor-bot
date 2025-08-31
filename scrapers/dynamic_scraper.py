from __future__ import annotations
from contextlib import contextmanager
from playwright.sync_api import sync_playwright
from .base_scraper import BaseScraper, ScrapeResult

class DynamicScraper(BaseScraper):
    def __init__(self, wait_until: str = "networkidle", timeout_ms: int = 30000):
        self.wait_until = wait_until
        self.timeout_ms = timeout_ms

    @contextmanager
    def _play(self):
        p = sync_playwright().start()
        try:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context()
            yield ctx
        finally:
            try:
                ctx.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass
            p.stop()

    def fetch(self, url: str) -> ScrapeResult:
        try:
            with self._play() as ctx:
                page = ctx.new_page()
                page.goto(url, wait_until=self.wait_until, timeout=self.timeout_ms)
                html = page.content()
                status = page.response.status if page.response else None
                return ScrapeResult(ok=True, status_code=status, html=html, url=url)
        except Exception as e:
            return ScrapeResult(ok=False, status_code=None, html=None, url=url, error=str(e))
