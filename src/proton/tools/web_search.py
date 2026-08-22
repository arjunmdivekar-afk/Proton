"""DuckDuckGo Web Search and URL content fetching tools for Proton."""

import re
from html import unescape
from typing import Any, Dict, List, Optional, Type
from urllib.parse import parse_qs, unquote, urlparse
import httpx
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel


class WebSearchInput(BaseModel):
    query: str = Field(description="Search query to look up on the web via DuckDuckGo")
    max_results: int = Field(default=5, description="Maximum number of search results to return (1-10)")


class FetchWebPageInput(BaseModel):
    url: str = Field(description="HTTP/HTTPS URL of the web page to fetch and read")
    max_chars: int = Field(default=4000, description="Maximum number of characters to extract from the page")


async def search_duckduckgo_async(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Execute search query against DuckDuckGo Lite endpoint."""
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://lite.duckduckgo.com/",
    }

    max_results = max(1, min(10, max_results))

    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            resp = await client.post(url, data={"q": query, "b": ""}, headers=headers)
            if resp.status_code != 200:
                return [{"title": "Search Error", "url": "", "snippet": f"DuckDuckGo returned HTTP {resp.status_code}"}]

            html = resp.text
            results: List[Dict[str, str]] = []

            # Extract result links and snippets from table rows
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

            # Fallback if class attribute structure differs
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

            for idx in range(min(len(link_matches), max_results)):
                raw_url, title_raw = link_matches[idx]
                title = unescape(re.sub(r"<[^>]+>", "", title_raw)).strip()

                # Unquote redirect URLs if needed
                actual_url = raw_url
                if "/l/?uddg=" in raw_url:
                    parsed = urlparse(raw_url)
                    qs = parse_qs(parsed.query)
                    if "uddg" in qs:
                        actual_url = unquote(qs["uddg"][0])

                snippet = ""
                if idx < len(snippet_matches):
                    snippet = unescape(re.sub(r"<[^>]+>", "", snippet_matches[idx])).strip()

                if title and actual_url:
                    results.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet,
                    })

            return results
    except Exception as e:
        return [{"title": "Search Error", "url": "", "snippet": f"Failed to query web search: {e}"}]


class DuckDuckGoSearchTool(BaseTool):
    """Search the web for real-time information using DuckDuckGo."""

    name = "duckduckgo_search"
    description = (
        "Search the web using DuckDuckGo to find real-time documentation, answers, libraries, "
        "APIs, error solutions, and latest information. Returns titles, URLs, and text snippets."
    )
    risk_level = RiskLevel.SAFE
    args_schema: Optional[Type[BaseModel]] = WebSearchInput

    async def run(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        results = await search_duckduckgo_async(query, max_results=max_results)
        return {
            "query": query,
            "results_count": len(results),
            "results": results,
        }


class FetchWebPageTool(BaseTool):
    """Fetch and extract readable plain text content from a web URL."""

    name = "fetch_web_page"
    description = "Fetch a web page URL and extract its clean readable text content."
    risk_level = RiskLevel.SAFE
    args_schema: Optional[Type[BaseModel]] = FetchWebPageInput

    async def run(self, url: str, max_chars: int = 4000) -> Dict[str, Any]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return {"url": url, "error": f"HTTP {resp.status_code}"}

                html = resp.text
                # Remove scripts, styles, head
                html = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", html, flags=re.IGNORECASE)
                html = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", "", html, flags=re.IGNORECASE)
                html = re.sub(r"<head\b[^<]*(?:(?!<\/head>)<[^<]*)*<\/head>", "", html, flags=re.IGNORECASE)

                text = unescape(re.sub(r"<[^>]+>", " ", html))
                text = re.sub(r"\s+", " ", text).strip()
                return {
                    "url": url,
                    "content": text[:max_chars],
                    "total_length": len(text),
                }
        except Exception as e:
            return {"url": url, "error": f"Failed to fetch {url}: {e}"}
