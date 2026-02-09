from __future__ import annotations

import json
import re
import time
from collections import deque
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse

import requests

from .data_sources import (
    DEFAULT_SEED_URLS,
    GASTRIC_KEYWORDS,
    NEGATIVE_TOPIC_KEYWORDS,
    NOISE_URL_HINTS,
    URL_TOPIC_HINTS,
    allowed_domains,
)


@dataclass
class CrawlResult:
    url: str
    title: str
    content: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.links.append(value)
                break


class GastricCrawler:
    def __init__(
        self, user_agent: str = "GastricRAGBot/1.0 (+local research use)"
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def crawl(
        self,
        max_pages: int = 120,
        min_chars: int = 500,
        sleep_seconds: float = 0.3,
        seed_urls: list[str] | None = None,
        on_progress: Callable[[int, int, int, int, str], None] | None = None,
    ) -> list[CrawlResult]:
        seeds = seed_urls or DEFAULT_SEED_URLS
        domain_allowlist = allowed_domains(seeds)

        queue = deque(seeds)
        visited: set[str] = set()
        results: list[CrawlResult] = []

        while queue and len(results) < max_pages:
            current_url = queue.popleft()
            normalized = self._normalize_url(current_url)
            if not normalized or normalized in visited:
                continue
            visited.add(normalized)

            if not self._domain_allowed(normalized, domain_allowlist):
                continue
            if self._is_noise_url(normalized):
                continue

            html = self._fetch_html(normalized)
            if not html:
                continue

            title, content = self._extract_text(normalized, html)
            if len(content) >= min_chars and self._is_gastric_related(title, content):
                results.append(
                    CrawlResult(url=normalized, title=title, content=content)
                )

            for link in self._extract_links(normalized, html):
                normalized_link = self._normalize_url(link)
                if (
                    normalized_link
                    and normalized_link not in visited
                    and not self._is_noise_url(normalized_link)
                    and self._is_likely_gastric_link(normalized_link)
                ):
                    queue.append(normalized_link)

            if on_progress:
                on_progress(
                    len(results),
                    max_pages,
                    len(visited),
                    len(queue),
                    normalized,
                )

            time.sleep(sleep_seconds)

        return results

    def save_jsonl(self, docs: list[CrawlResult], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            for doc in docs:
                f.write(
                    json.dumps(
                        {"url": doc.url, "title": doc.title, "content": doc.content},
                        ensure_ascii=False,
                    )
                )
                f.write("\n")

    def _fetch_html(self, url: str) -> str | None:
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return None
            return response.text
        except requests.RequestException:
            return None

    def _extract_text(self, url: str, html: str) -> tuple[str, str]:
        title = self._extract_title(html) or url
        content = self._extract_plain_text(html)
        return title, content

    def _extract_links(self, base_url: str, html: str) -> list[str]:
        parser = _LinkParser()
        parser.feed(html)
        found: list[str] = []
        for raw_href in parser.links:
            href = raw_href.strip()
            if not href:
                continue
            absolute = urljoin(base_url, href)
            if absolute.startswith("http"):
                found.append(absolute)
        return found

    @staticmethod
    def _extract_title(html: str) -> str:
        match = re.search(
            r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL
        )
        if not match:
            return ""
        text = re.sub(r"\s+", " ", match.group(1)).strip()
        return unescape(text)

    @staticmethod
    def _extract_plain_text(html: str) -> str:
        cleaned = re.sub(
            r"<script[\s\S]*?</script>|<style[\s\S]*?</style>",
            " ",
            html,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _normalize_url(url: str) -> str | None:
        try:
            parsed = urlparse(url)
        except ValueError:
            return None
        if parsed.scheme not in {"http", "https"}:
            return None
        clean = parsed._replace(fragment="")
        return clean.geturl().rstrip("/")

    @staticmethod
    def _domain_allowed(url: str, allowlist: set[str]) -> bool:
        netloc = urlparse(url).netloc
        return any(
            netloc == domain or netloc.endswith(f".{domain}") for domain in allowlist
        )

    @staticmethod
    def _is_gastric_related(title: str, content: str) -> bool:
        title_text = title.lower()
        if any(word in title_text for word in NEGATIVE_TOPIC_KEYWORDS):
            return False

        scoped = f"{title}\n{content[:1500]}".lower()
        return any(keyword.lower() in scoped for keyword in GASTRIC_KEYWORDS)

    @staticmethod
    def _is_noise_url(url: str) -> bool:
        lowered = url.lower()
        return any(hint in lowered for hint in NOISE_URL_HINTS)

    @staticmethod
    def _is_likely_gastric_link(url: str) -> bool:
        lowered = url.lower()
        return any(hint in lowered for hint in URL_TOPIC_HINTS)
