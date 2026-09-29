"""Small, dependency-light research helper used by the /web command."""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urlparse

import httpx
from ddgs import DDGS


async def fetch_clean_page(
    client: httpx.AsyncClient, url: str, fallback_snippet: str
) -> str:
    try:
        response = await client.get(f"https://r.jina.ai/{url}", timeout=8.0)
        if response.status_code == 200 and len(response.text) > 80:
            return re.sub(r"\s+", " ", response.text).strip()[:2_000]
    except httpx.HTTPError:
        pass
    return fallback_snippet


def score_relevance(query: str, title: str, text: str) -> float:
    query_words = set(re.findall(r"\b\w{2,}\b", query.casefold()))

    def count(target: str) -> int:
        words = re.findall(r"\b\w+\b", target.casefold())
        return sum(words.count(word) for word in query_words)

    return float(count(title) * 3 + count(text))


async def conduct_deep_research(
    query: str, max_sites: int = 10, top_filtered: int = 4
) -> dict:
    try:
        raw_results = await asyncio.to_thread(
            lambda: list(DDGS().text(query, max_results=max_sites))
        )
    except Exception as exc:
        return {
            "brief": "",
            "sources": [],
            "error": f"Search could not be completed: {exc}",
        }

    results = [
        item for item in raw_results if item.get("href") or item.get("link")
    ]
    if not results:
        return {"brief": "", "sources": [], "error": "No search results found."}

    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "Nexus/0.2 (+local desktop assistant)"},
    ) as client:
        pages = await asyncio.gather(
            *(
                fetch_clean_page(
                    client,
                    item.get("href") or item.get("link", ""),
                    item.get("body", ""),
                )
                for item in results
            )
        )

    scored = sorted(
        zip(results, pages, strict=True),
        key=lambda pair: score_relevance(query, pair[0].get("title", ""), pair[1]),
        reverse=True,
    )[:top_filtered]

    sources = []
    brief_parts = []
    for index, (item, page) in enumerate(scored, start=1):
        link = item.get("href") or item.get("link", "")
        title = item.get("title") or urlparse(link).netloc
        excerpt = re.sub(r"\s+", " ", page).strip()[:1_200]
        sources.append({"title": title, "link": link, "snippet": excerpt})
        brief_parts.append(f"[{index}] {title}\nURL: {link}\nExcerpt: {excerpt}")

    return {"brief": "\n\n".join(brief_parts), "sources": sources}
