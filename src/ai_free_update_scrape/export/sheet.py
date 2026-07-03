"""Exports for Google Sheets and quick local review."""

from __future__ import annotations

import csv
from pathlib import Path


def write_articles_csv(articles: list[dict], output_path: Path) -> Path:
    """Write article rows to a Sheets-friendly CSV."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "published",
        "scraped_at",
        "source",
        "title",
        "url",
        "summary",
        "topics",
        "new_tool",
        "tool_type",
        "tool_name",
        "top_score",
        "reason",
        "alternatives",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            detection = article.get("detection", {})
            ranking = article.get("ranking", {})
            writer.writerow({
                "published": article.get("published", ""),
                "scraped_at": article.get("scraped_at", ""),
                "source": article.get("source", ""),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "summary": article.get("summary", ""),
                "topics": ", ".join(article.get("topics", [])),
                "new_tool": detection.get("new_tool", False),
                "tool_type": detection.get("type", ""),
                "tool_name": detection.get("tool_name", ""),
                "top_score": ranking.get("top_score", 0),
                "reason": ranking.get("reason", ""),
                "alternatives": " | ".join(
                    f"{alt.get('name', '')} ({alt.get('github', '')})"
                    for alt in article.get("alternatives", [])
                ),
            })
    return output_path


def write_dashboard_html(
    digest_path: Path,
    shorts_csv: Path,
    articles_csv: Path,
    output_path: Path,
) -> Path:
    """Create a simple local landing page for the day's outputs."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>AI Free Update Scrape Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 32px; max-width: 980px; margin: auto; background: #0b1020; color: #e8ecf7; }}
    a {{ color: #8dd6ff; }}
    .card {{ background: #121933; border: 1px solid #243055; border-radius: 14px; padding: 18px; margin: 18px 0; }}
    code {{ background: #1b2444; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>AI Free Update Scrape</h1>
  <div class="card">
    <p>Digest: <a href="{digest_path.name}">{digest_path.name}</a></p>
    <p>Articles sheet CSV: <a href="{articles_csv.name}">{articles_csv.name}</a></p>
    <p>Shorts plan CSV: <a href="{shorts_csv.name}">{shorts_csv.name}</a></p>
  </div>
  <div class="card">
    <p>Import the CSV files into Google Sheets, then use the digest for the script source and the shorts plan for the 60-day queue.</p>
  </div>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path
