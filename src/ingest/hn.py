"""Hacker News top stories scraper via Firebase API."""
import httpx
from datetime import datetime, timezone


HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch_hn_top(limit: int = 30) -> list[dict]:
    ids = httpx.get(HN_TOP, timeout=10).json()[:limit]
    articles = []
    for story_id in ids:
        try:
            item = httpx.get(HN_ITEM.format(story_id), timeout=10).json()
            if item and item.get("url"):
                articles.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "summary": f"HN score: {item.get('score', 0)} | comments: {item.get('descendants', 0)}",
                    "published": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc).isoformat(),
                    "topics": ["agents", "builders"],
                    "source": "Hacker News",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            pass
    return articles
