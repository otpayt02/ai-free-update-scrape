"""Source catalog and topic utilities for AI news and free-tool tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class SourceGroup:
    """A named source group with a short description and topic tags."""

    name: str
    tags: tuple[str, ...]
    description: str


TOPIC_GROUPS: tuple[SourceGroup, ...] = (
    SourceGroup("models", ("models", "multimodal", "audio", "video", "image"), "Model releases and capability jumps"),
    SourceGroup("agents", ("agents", "mcp", "tools", "skills", "workflows"), "Agent frameworks and tool hookups"),
    SourceGroup("builders", ("github", "source code", "repo", "sdk", "api"), "Source code, SDKs, and repo launches"),
    SourceGroup("free", ("free", "open source", "oss", "open-source", "free tier"), "Free tiers and open-source alternatives"),
    SourceGroup("policy", ("policy", "government", "regulation", "safety"), "Government and policy updates"),
    SourceGroup("product", ("launch", "integration", "feature", "update"), "Product launches and feature changes"),
)


TIME_WINDOWS = {
    "morning": {"label": "Morning", "slot": "01:00"},
    "midday": {"label": "Midday", "slot": "12:00"},
    "night": {"label": "Night", "slot": "21:00"},
}


def classify_topics(text: str) -> list[str]:
    """Assign broad topic buckets so downstream ranking is less keyword-blind."""

    lowered = text.lower()
    topics = [group.name for group in TOPIC_GROUPS if any(tag in lowered for tag in group.tags)]
    return topics or ["general"]


def build_query_terms() -> list[str]:
    """Return broad source-discovery terms for manual source expansion."""

    return [
        "AI model release",
        "open source AI tool",
        "free tier AI product",
        "MCP integration",
        "agent framework",
        "multimodal model",
        "AI government update",
        "GitHub AI repo",
        "AI video generation",
        "AI audio generation",
    ]


def time_slot_for_now(now: datetime | None = None) -> str:
    """Map the current time to one of the three daily scrape windows."""

    now = now or datetime.now()
    hour = now.hour
    if hour < 9:
        return "morning"
    if hour < 18:
        return "midday"
    return "night"


def iter_topic_labels(topics: Iterable[str]) -> list[str]:
    """Normalize topic labels for display and exports."""

    return [topic.replace("_", " ").title() for topic in topics]
