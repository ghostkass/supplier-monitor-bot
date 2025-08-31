from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

@dataclass
class ScrapeResult:
    ok: bool
    status_code: Optional[int]
    html: Optional[str]
    url: str
    error: Optional[str] = None

class BaseScraper:
    def fetch(self, url: str):
        raise NotImplementedError

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html, "lxml")
        except Exception:
            # fallback Windows/Python 3.13 : pas de lxml -> parser standard
            return BeautifulSoup(html, "html.parser")
