"""Session parameters and selection rules for scrape runs."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class SessionProfile:
    """The default scrape session profile exposed in the dashboard."""

    min_items: int = 20
    ai_industry_items: int = 15
    free_items: int = 5
    max_items_per_run: int = 60
    rss_limit: int = 20
    hn_limit: int = 30
    web_limit: int = 20
    top_articles_limit: int = 50
    shortlist_limit: int = 20
    plan_days: int = 60
    plan_per_day: int = 4
    llm_model: str = ""

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary for the UI."""

        return asdict(self)


DEFAULT_SESSION = SessionProfile()


def score_session_priority(article: dict) -> tuple[int, int, int]:
    """Rank items for session selection by strategic value."""

    topics = article.get("topics", []) or []
    detection = article.get("detection", {}) or {}
    ranking = article.get("ranking", {}) or {}
    is_free = 1 if "free" in topics or detection.get("type") == "free" else 0
    is_industry = 1 if any(topic in topics for topic in ("models", "agents", "builders", "product", "policy")) else 0
    score = int(ranking.get("top_score", 0) or 0)
    return (is_industry, is_free, score)


def select_session_items(articles: list[dict], profile: SessionProfile = DEFAULT_SESSION) -> dict[str, list[dict]]:
    """Select the 15+5 session mix and return the rationale buckets."""

    ranked = sorted(articles, key=score_session_priority, reverse=True)
    industry_pool = [article for article in ranked if any(topic in (article.get("topics", []) or []) for topic in ("models", "agents", "builders", "product", "policy"))]
    free_pool = [article for article in ranked if "free" in (article.get("topics", []) or []) or article.get("detection", {}).get("type") == "free"]
    selected_industry = industry_pool[:profile.ai_industry_items]
    selected_free = []
    for article in free_pool:
        if article not in selected_industry:
            selected_free.append(article)
        if len(selected_free) >= profile.free_items:
            break
    selected = (selected_industry + selected_free)[: profile.min_items]
    return {
        "selected": selected,
        "industry": selected_industry,
        "free": selected_free,
    }
