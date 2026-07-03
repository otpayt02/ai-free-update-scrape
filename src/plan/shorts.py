"""Shorts planning helpers for turning ranked AI updates into a content calendar."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from ..catalog import classify_topics, iter_topic_labels


@dataclass(frozen=True)
class ShortsEntry:
    """One row in the Shorts content plan."""

    publish_date: str
    slot: str
    angle: str
    hook: str
    source_title: str
    url: str
    topics: str
    score: int
    summary: str
    free_angle: str


ANGLE_LIBRARY = {
    "models": "What changed in the model and why it matters now",
    "agents": "What this unlocks for agent workflows and automations",
    "builders": "Why builders and devs should care about the release",
    "free": "How to use the free path, open-source option, or free tier",
    "policy": "What this means for builders, companies, or creators",
    "product": "What changed in the product and the new use case it opens",
    "general": "The single most useful takeaway in under 60 seconds",
}


def _pick_angle(topics: list[str]) -> str:
    for topic in topics:
        if topic in ANGLE_LIBRARY:
            return ANGLE_LIBRARY[topic]
    return ANGLE_LIBRARY["general"]


def _pick_hook(title: str, topics: list[str], free_alternative_count: int) -> str:
    prefix = "Free AI update" if "free" in topics else "AI update"
    if free_alternative_count:
        return f"{prefix}: {title} and {free_alternative_count} free option(s) to watch"
    return f"{prefix}: {title}"


def build_shorts_plan(
    ranked_articles: list[dict],
    days: int = 60,
    per_day: int = 4,
) -> list[ShortsEntry]:
    """Convert ranked articles into a repeatable 60-day Shorts queue."""

    sorted_articles = sorted(
        ranked_articles,
        key=lambda article: (
            article.get("ranking", {}).get("top_score", 0),
            len(article.get("alternatives", []) or []),
        ),
        reverse=True,
    )
    selected = [article for article in sorted_articles if article.get("detection", {}).get("new_tool")]
    plan: list[ShortsEntry] = []
    start = date.today()

    if not selected:
        return plan

    total_slots = days * per_day
    for slot_index in range(total_slots):
        article = selected[slot_index % len(selected)]
        topics = classify_topics(" ".join([
            article.get("title", ""),
            article.get("summary", ""),
            article.get("source", ""),
            article.get("detection", {}).get("tool_name", ""),
        ]))
        free_count = len(article.get("alternatives", []) or [])
        plan.append(
            ShortsEntry(
                publish_date=(start + timedelta(days=slot_index // per_day)).isoformat(),
                slot=["morning", "midday", "night", "bonus"][slot_index % per_day],
                angle=_pick_angle(topics),
                hook=_pick_hook(article.get("title", "Unknown"), topics, free_count),
                source_title=article.get("title", "Unknown"),
                url=article.get("url", ""),
                topics=", ".join(iter_topic_labels(topics)),
                score=int(article.get("ranking", {}).get("top_score", 0) or 0),
                summary=article.get("summary", "")[:220].replace("\n", " "),
                free_angle=article.get("ranking", {}).get("reason", "")[:220].replace("\n", " "),
            )
        )
    return plan


def write_shorts_csv(plan: list[ShortsEntry], output_path: Path) -> Path:
    """Write a Google Sheets-friendly CSV."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ShortsEntry.__annotations__.keys()))
        writer.writeheader()
        for row in plan:
            writer.writerow(row.__dict__)
    return output_path


def write_shorts_markdown(plan: list[ShortsEntry], output_path: Path) -> Path:
    """Write a quick human-readable planning sheet."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Shorts Plan", ""]
    for row in plan[:30]:
        lines.extend([
            f"## {row.publish_date} {row.slot}",
            f"- Angle: {row.angle}",
            f"- Hook: {row.hook}",
            f"- Source: {row.source_title}",
            f"- Topics: {row.topics}",
            f"- Score: {row.score}",
            f"- URL: {row.url}",
            "",
        ])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
