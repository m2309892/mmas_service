"""Internet search and page fetching for RAG enrichment."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qs, unquote, urlparse


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""


@dataclass(frozen=True)
class WebDocument:
    title: str
    url: str
    text: str


class SearchClient(Protocol):
    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        ...


def _strip_tags(value: str) -> str:
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _clean_duckduckgo_url(url: str) -> str:
    decoded = html.unescape(url)
    parsed = urlparse(decoded)
    query = parse_qs(parsed.query)
    if "uddg" in query:
        return unquote(query["uddg"][0])
    return decoded


class DuckDuckGoLiteSearchClient:
    """Small HTML search client.

    This is a replaceable prototype adapter. For production, prefer a paid search
    API with stable terms and structured responses.
    """

    def __init__(self, *, timeout: float = 20.0) -> None:
        self.timeout = timeout

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("Install ML/rag_chatbot/requirements.txt to search the web") from exc

        params = {"q": query}
        headers = {"User-Agent": "MMAS-RAG-Prototype/0.1"}
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get("https://duckduckgo.com/html/", params=params, headers=headers)
            response.raise_for_status()
            body = response.text

        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            flags=re.IGNORECASE | re.DOTALL,
        )
        results: list[SearchResult] = []
        for match in pattern.finditer(body):
            title = _strip_tags(match.group("title"))
            url = _clean_duckduckgo_url(match.group("href"))
            if title and url:
                results.append(SearchResult(title=title, url=url))
            if len(results) >= max_results:
                break
        return results


class WebPageFetcher:
    def __init__(self, *, timeout: float = 20.0, max_chars: int = 8000) -> None:
        self.timeout = timeout
        self.max_chars = max_chars

    async def fetch_text(self, url: str) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("Install ML/rag_chatbot/requirements.txt to fetch web pages") from exc

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
        headers = {"User-Agent": "MMAS-RAG-Prototype/0.1"}
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            text = _strip_tags(response.text)
        return text[: self.max_chars]


class InternetResearcher:
    def __init__(
        self,
        *,
        search_client: SearchClient | None = None,
        fetcher: WebPageFetcher | None = None,
    ) -> None:
        self.search_client = search_client or DuckDuckGoLiteSearchClient()
        self.fetcher = fetcher or WebPageFetcher()

    async def search_and_fetch(self, query: str, *, max_results: int) -> list[WebDocument]:
        results = await self.search_client.search(query, max_results=max_results)
        documents: list[WebDocument] = []
        for result in results:
            try:
                text = await self.fetcher.fetch_text(result.url)
            except Exception:
                continue
            if text:
                documents.append(WebDocument(title=result.title, url=result.url, text=text))
        return documents
