"""Lightweight non-RSS scrapers for the free AI radar."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup


def fetch_github_trending(url: str, name: str) -> list[dict]:
    """Scrape GitHub Trending with a simple HTML parser."""

    response = httpx.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for item in soup.select("article.Box-row")[:15]:
        link = item.select_one("h2 a")
        if not link:
            continue
        href = link.get("href", "")
        repo_url = f"https://github.com{href}" if href.startswith("/") else href
        title = " ".join(link.get_text(" ", strip=True).split())
        desc = item.select_one("p")
        articles.append({
            "title": title,
            "url": repo_url,
            "summary": desc.get_text(" ", strip=True) if desc else "",
            "published": datetime.now(timezone.utc).isoformat(),
            "topics": ["builders", "free"],
            "source": name,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return articles


def fetch_reddit_json(url: str, name: str) -> list[dict]:
    """Fetch a Reddit JSON listing with a browser-like user agent."""

    response = httpx.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    payload = response.json()
    articles = []
    for child in payload.get("data", {}).get("children", [])[:15]:
        data = child.get("data", {})
        articles.append({
            "title": data.get("title", ""),
            "url": f"https://www.reddit.com{data.get('permalink', '')}",
            "summary": data.get("selftext", "") or data.get("subreddit_name_prefixed", ""),
            "published": datetime.fromtimestamp(data.get("created_utc", 0), tz=timezone.utc).isoformat(),
            "topics": ["general"],
            "source": name,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return articles


def fetch_arxiv_recent(url: str, name: str) -> list[dict]:
    """Scrape arXiv recent listings with HTML selectors."""

    response = httpx.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    rows = soup.select("dl > dt")
    for row in rows[:20]:
        link = row.select_one("a[title='Abstract']")
        if not link:
            continue
        abstract_id = link.get_text(strip=True)
        title_row = row.find_next_sibling("dd")
        title = title_row.select_one("div.list-title") if title_row else None
        summary = title_row.select_one("p") if title_row else None
        articles.append({
            "title": title.get_text(" ", strip=True).replace("Title: ", "") if title else abstract_id,
            "url": f"https://arxiv.org{link.get('href', '')}",
            "summary": summary.get_text(" ", strip=True) if summary else "",
            "published": datetime.now(timezone.utc).isoformat(),
            "topics": ["builders", "models"],
            "source": name,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return articles


def fetch_source(source: dict) -> list[dict]:
    """Route a source definition to the matching scraper."""

    source_type = source.get("type", "rss")
    url = source.get("url", "")
    name = source.get("name", url)
    if source_type == "github_trending":
        return fetch_github_trending(url, name)
    if source_type == "reddit_json":
        return fetch_reddit_json(url, name)
    if source_type == "arxiv":
        return fetch_arxiv_recent(url, name)
    return []
