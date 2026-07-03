"""RSS + ATOM feed scraper using feedparser."""
import feedparser
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def fetch_feed(url: str) -> list[dict[str, Any]]:
    """Fetch and parse an RSS/ATOM feed. Returns list of article dicts."""
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", ""),
            "topics": [],
            "source": feed.feed.get("title", url),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return articles


def run_rss_ingest(sources: list[dict], output_path: Path) -> int:
    """Fetch all RSS sources, append new articles to output_path as JSONL."""
    seen_urls: set[str] = set()
    if output_path.exists():
        for line in output_path.read_text().splitlines():
            try:
                seen_urls.add(json.loads(line)["url"])
            except Exception:
                pass

    new_count = 0
    with output_path.open("a") as f:
        for source in sources:
            if source.get("type", "rss") not in ("rss", None, ""):
                continue
            try:
                articles = fetch_feed(source["url"])
                for article in articles:
                    article["source"] = source.get("name", article.get("source", ""))
                    if article["url"] not in seen_urls:
                        f.write(json.dumps(article) + "\n")
                        seen_urls.add(article["url"])
                        new_count += 1
            except Exception as e:
                print(f"[rss] error fetching {source['url']}: {e}")
    return new_count
