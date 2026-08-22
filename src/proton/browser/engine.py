"""Core navigation, search, and page parsing engine for Proton Browser."""

import re
from dataclasses import dataclass, field
from html import unescape
from typing import Dict, List, Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse
import httpx


@dataclass
class BrowserLink:
    index: int
    text: str
    url: str
    snippet: str = ""


@dataclass
class BrowserPage:
    url: str
    title: str
    content: str
    links: List[BrowserLink] = field(default_factory=list)
    is_search: bool = False
    query: str = ""
    status_code: int = 200
    error: Optional[str] = None


class ProtonBrowserEngine:
    """Headless browser engine that fetches, extracts, and manages page state."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"

    def __init__(self) -> None:
        self.history: List[BrowserPage] = []
        self.history_index: int = -1

    @property
    def current_page(self) -> Optional[BrowserPage]:
        if 0 <= self.history_index < len(self.history):
            return self.history[self.history_index]
        return None

    @property
    def can_go_back(self) -> bool:
        return self.history_index > 0

    @property
    def can_go_forward(self) -> bool:
        return self.history_index < len(self.history) - 1

    def go_back(self) -> Optional[BrowserPage]:
        if self.can_go_back:
            self.history_index -= 1
            return self.current_page
        return None

    def go_forward(self) -> Optional[BrowserPage]:
        if self.can_go_forward:
            self.history_index += 1
            return self.current_page
        return None

    def _push_page(self, page: BrowserPage) -> None:
        # Truncate forward history if navigating to a new branch
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]
        self.history.append(page)
        self.history_index = len(self.history) - 1

    async def search(self, query: str, max_results: int = 10) -> BrowserPage:
        """Execute web search via DuckDuckGo and return formatted search results page."""
        url = "https://lite.duckduckgo.com/lite/"
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://lite.duckduckgo.com/",
        }

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.post(url, data={"q": query, "b": ""}, headers=headers)
                if resp.status_code != 200:
                    page = BrowserPage(
                        url=f"ddg://search?q={query}",
                        title=f"Search Error: {query}",
                        content=f"DuckDuckGo returned HTTP {resp.status_code}",
                        is_search=True,
                        query=query,
                        status_code=resp.status_code,
                        error=f"HTTP {resp.status_code}",
                    )
                    self._push_page(page)
                    return page

                html = resp.text
                link_matches = re.findall(
                    r'<a[^>]+class=[\'"]result-link[\'"][^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
                snippet_matches = re.findall(
                    r'<td[^>]+class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>',
                    html,
                    re.DOTALL | re.IGNORECASE,
                )

                if not link_matches:
                    raw_links = re.findall(
                        r'<a[^>]+href=[\'"](https?://[^\'"]+)[\'"][^>]*>(.*?)</a>',
                        html,
                        re.DOTALL,
                    )
                    link_matches = [
                        (l_url, l_text)
                        for l_url, l_text in raw_links
                        if "duckduckgo.com" not in l_url and not l_url.startswith("/")
                    ]

                browser_links: List[BrowserLink] = []
                content_lines: List[str] = [f"# DuckDuckGo Search Results: {query}\n"]

                for idx in range(min(len(link_matches), max_results)):
                    raw_url, title_raw = link_matches[idx]
                    title = unescape(re.sub(r"<[^>]+>", "", title_raw)).strip()

                    actual_url = raw_url
                    if "/l/?uddg=" in raw_url:
                        parsed = urlparse(raw_url)
                        qs = parse_qs(parsed.query)
                        if "uddg" in qs:
                            actual_url = unquote(qs["uddg"][0])

                    snippet = ""
                    if idx < len(snippet_matches):
                        snippet = unescape(re.sub(r"<[^>]+>", "", snippet_matches[idx])).strip()

                    link_item = BrowserLink(
                        index=idx + 1,
                        text=title,
                        url=actual_url,
                        snippet=snippet,
                    )
                    browser_links.append(link_item)
                    content_lines.append(f"### [{idx + 1}] {title}")
                    content_lines.append(f"**URL:** `{actual_url}`")
                    if snippet:
                        content_lines.append(f"{snippet}\n")

                if not browser_links:
                    content_lines.append("No results found for your query. Try different keywords.")

                page = BrowserPage(
                    url=f"ddg://search?q={query}",
                    title=f"Search: {query}",
                    content="\n".join(content_lines),
                    links=browser_links,
                    is_search=True,
                    query=query,
                    status_code=200,
                )
                self._push_page(page)
                return page

        except Exception as e:
            page = BrowserPage(
                url=f"ddg://search?q={query}",
                title=f"Search Error: {query}",
                content=f"Error connecting to DuckDuckGo: {e}",
                is_search=True,
                query=query,
                error=str(e),
            )
            self._push_page(page)
            return page

    async def navigate(self, target: str) -> BrowserPage:
        """Navigate to a URL or execute search if input is not a valid URL."""
        target = target.strip()
        if not target:
            return self.current_page or BrowserPage(url="", title="Empty", content="")

        # Check if target is a search query or URL
        is_url = bool(re.match(r"^(https?://|[a-zA-Z0-9_\-]+\.[a-zA-Z]{2,}(/.*)?$)", target))
        if not is_url:
            return await self.search(target)

        # Normalize URL scheme
        if not target.startswith(("http://", "https://")):
            target = "https://" + target

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(target, headers=headers)
                status_code = resp.status_code
                html = resp.text

                # Extract title
                title_match = re.search(r"<title\b[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
                title = unescape(title_match.group(1)).strip() if title_match else target

                # Extract all interactive links
                raw_links = re.findall(r"<a\b[^>]*href=[\'\"]([^\'\"]+)[\'\"][^>]*>(.*?)</a>", html, re.DOTALL | re.IGNORECASE)
                links: List[BrowserLink] = []
                seen_urls = set()

                link_index = 1
                for href, text_raw in raw_links:
                    clean_text = unescape(re.sub(r"<[^>]+>", "", text_raw)).strip()
                    full_url = urljoin(target, href)
                    if clean_text and full_url.startswith(("http://", "https://")) and full_url not in seen_urls:
                        seen_urls.add(full_url)
                        links.append(BrowserLink(index=link_index, text=clean_text, url=full_url))
                        link_index += 1
                        if len(links) >= 50:
                            break

                # Clean and extract plain text/markdown
                clean_html = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", "", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<head\b[^<]*(?:(?!<\/head>)<[^<]*)*<\/head>", "", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<nav\b[^<]*(?:(?!<\/nav>)<[^<]*)*<\/nav>", "", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<footer\b[^<]*(?:(?!<\/footer>)<[^<]*)*<\/footer>", "", clean_html, flags=re.IGNORECASE)

                # Format headings, lists, paragraphs
                clean_html = re.sub(r"<h1\b[^>]*>(.*?)<\/h1>", r"\n# \1\n", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<h2\b[^>]*>(.*?)<\/h2>", r"\n## \1\n", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<h3\b[^>]*>(.*?)<\/h3>", r"\n### \1\n", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<li\b[^>]*>(.*?)<\/li>", r"\n• \1", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<p\b[^>]*>(.*?)<\/p>", r"\n\1\n", clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r"<br\s*\/?>", r"\n", clean_html, flags=re.IGNORECASE)

                # Strip remaining tags
                body_text = unescape(re.sub(r"<[^>]+>", "", clean_html))
                # Remove excessive blank lines
                body_text = re.sub(r"\n{3,}", "\n\n", body_text).strip()

                page = BrowserPage(
                    url=str(resp.url),
                    title=title,
                    content=body_text[:12000],
                    links=links,
                    status_code=status_code,
                )
                self._push_page(page)
                return page

        except Exception as e:
            page = BrowserPage(
                url=target,
                title=f"Failed to load {target}",
                content=f"Error loading web page: {e}",
                status_code=0,
                error=str(e),
            )
            self._push_page(page)
            return page

    async def open_link_by_index(self, index: int) -> Optional[BrowserPage]:
        """Navigate to a link by its numbered index on the current page."""
        if not self.current_page:
            return None

        for link in self.current_page.links:
            if link.index == index:
                return await self.navigate(link.url)

        return None
