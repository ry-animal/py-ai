from __future__ import annotations

import httpx

from app.config import get_settings


class TavilySearch:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY not set in environment")

    async def search(self, query: str) -> list[str]:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "max_results": self.settings.max_web_results,
            "search_depth": self.settings.tavily_search_depth,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
        except httpx.HTTPError:
            return ["[web search: request failed]"]
        snippets: list[str] = []
        for item in data.get("results", [])[: self.settings.max_web_results]:
            title = item.get("title") or ""
            snippet = item.get("content") or ""
            url = item.get("url") or ""
            text = snippet or title
            if text:
                snippets.append(f"{text} (source: {url})" if url else text)
        return snippets or ["[web search: no results found]"]

    async def search_with_answer(self, query: str) -> tuple[list[str], str | None]:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "max_results": self.settings.max_web_results,
            "search_depth": self.settings.tavily_search_depth,
            "include_answer": True,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
        except httpx.HTTPError:
            return ["[web search: request failed]"], None

        snippets: list[str] = []
        for item in data.get("results", [])[: self.settings.max_web_results]:
            title = item.get("title") or ""
            snippet = item.get("content") or ""
            link = item.get("url") or ""
            text = snippet or title
            if text:
                snippets.append(f"{text} (source: {link})" if link else text)
        answer = data.get("answer") or None
        return (snippets, answer)
