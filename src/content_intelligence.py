"""Evidence-first audience, content-pillar, format, and idea ranking helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import yaml


AUDIENCE_TAXONOMY = (
    {
        "id": "solo_freelancers_operators",
        "label": "Solo freelancers & operators",
        "keywords": ("client onboarding", "invoicing", "proposal", "crm", "time tracking", "freelance", "solo operator", "client work"),
    },
    {
        "id": "vibe_coders",
        "label": "Vibe coders",
        "keywords": ("cursor", "v0.dev", "bolt.new", "prompt engineering", "no code", "low code", "ai coding", "vibe coding"),
    },
    {
        "id": "developers",
        "label": "Developers",
        "keywords": ("api", "rate limit", "ci/cd", "pipeline", "docker", "dependency", "refactor", "sdk", "repository", "github", "debug"),
    },
    {
        "id": "small_businesses",
        "label": "Small businesses",
        "keywords": ("lead generation", "support bot", "inventory", "social scheduling", "small business", "customer support", "sales workflow"),
    },
    {
        "id": "corporate_individuals",
        "label": "Corporate professionals",
        "keywords": ("excel", "spreadsheet", "pdf extraction", "outlook", "meeting", "microsoft 365", "reporting", "data entry", "corporate"),
    },
    {
        "id": "creators_educators",
        "label": "Creators & educators",
        "keywords": ("youtube", "creator", "video", "content", "course", "tutorial", "audience", "newsletter"),
    },
    {
        "id": "general_productivity",
        "label": "Everyday productivity users",
        "keywords": ("productivity", "workflow", "save time", "organize", "repeatable", "efficiency"),
    },
)


CONTENT_PILLARS = (
    {"id": "news_updates", "label": "AI & tech news updates", "keywords": ("announce", "release", "launch", "update", "new model", "breaking", "research", "policy")},
    {"id": "tips_tricks", "label": "Tips & tricks", "keywords": ("shortcut", "hack", "tip", "trick", "hidden feature", "faster", "quick way")},
    {"id": "pain_point_solutions", "label": "Pain-point solutions", "keywords": ("error", "failed", "stuck", "problem", "bug", "doesn't work", "cannot", "missing", "slow", "frustrat")},
    {"id": "manual_task_automation", "label": "Manual-task automation", "keywords": ("manual", "automate", "automation", "cron", "background process", "data entry", "repetitive")},
    {"id": "concepts_education", "label": "Concept education", "keywords": ("what is", "how it works", "explained", "difference between", "concept", "understand", "why does")},
    {"id": "tool_instructions", "label": "Tool instructions", "keywords": ("tutorial", "setup", "getting started", "how to use", "install", "configure", "documentation")},
    {"id": "systems_mindset", "label": "Systems mindset & motivation", "keywords": ("system", "mindset", "leverage", "standard operating", "sop", "consistency", "motivat", "builder friction")},
    {"id": "use_cases_portfolio", "label": "Use cases & portfolio showcases", "keywords": ("case study", "built", "portfolio", "project", "mvp", "workflow test", "demo", "showcase")},
    {"id": "promotions_offers", "label": "Products, affiliates & backend offers", "keywords": ("template", "toolkit", "consult", "service", "affiliate", "product", "offer", "download", "hire")},
    {"id": "comparisons_reviews", "label": "Comparisons & reviews", "keywords": ("versus", " vs ", "compare", "comparison", "review", "alternative", "best tool", "worth it")},
)


SCORING_WEIGHTS = {
    "keyword_growth_velocity": 0.4,
    "source_engagement": 0.3,
    "monetization_intent": 0.3,
}


def load_strategy(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _record_text(record: dict) -> str:
    values = [
        record.get("title", ""),
        record.get("summary", ""),
        record.get("text", ""),
        record.get("body", ""),
        record.get("source", ""),
        " ".join(str(value) for value in record.get("topics", []) or []),
        " ".join(str(value) for value in record.get("categories", []) or []),
    ]
    return re.sub(r"\s+", " ", " ".join(str(value) for value in values)).strip().lower()


def _taxonomy_matches(text: str, taxonomy: Iterable[dict]) -> list[dict]:
    scored = []
    for item in taxonomy:
        hits = sorted({keyword for keyword in item["keywords"] if keyword in text})
        if hits:
            scored.append({"id": item["id"], "label": item["label"], "score": len(hits), "matched_keywords": hits})
    return sorted(scored, key=lambda row: (-row["score"], row["label"]))


def classify_record(record: dict) -> dict:
    """Classify a normalized article, question, issue, comment, or imported review."""
    text = _record_text(record)
    audience_matches = _taxonomy_matches(text, AUDIENCE_TAXONOMY)
    pillar_matches = _taxonomy_matches(text, CONTENT_PILLARS)
    pain_source_kinds = {"stackexchange_question", "github_issue", "youtube_comment", "reddit_post", "approved_review_import"}
    is_pain_signal = bool(record.get("pain_signal")) or str(record.get("source_kind", "")) in pain_source_kinds
    if not audience_matches:
        fallback = next(item for item in AUDIENCE_TAXONOMY if item["id"] == "general_productivity")
        audience_matches = [{"id": fallback["id"], "label": fallback["label"], "score": 0, "matched_keywords": []}]
    if is_pain_signal:
        pain_match = next((row for row in pillar_matches if row["id"] == "pain_point_solutions"), None)
        if pain_match is None:
            fallback = next(item for item in CONTENT_PILLARS if item["id"] == "pain_point_solutions")
            pain_match = {"id": fallback["id"], "label": fallback["label"], "score": 0, "matched_keywords": ["source pain signal"]}
            pillar_matches.append(pain_match)
        elif "source pain signal" not in pain_match["matched_keywords"]:
            pain_match["matched_keywords"].append("source pain signal")
        pain_match["score"] = max([row["score"] for row in pillar_matches] + [0]) + 1
        pillar_matches = sorted(pillar_matches, key=lambda row: (-row["score"], row["label"]))
    elif not pillar_matches:
        fallback_id = "news_updates"
        fallback = next(item for item in CONTENT_PILLARS if item["id"] == fallback_id)
        pillar_matches = [{"id": fallback["id"], "label": fallback["label"], "score": 0, "matched_keywords": []}]

    primary_pillar = pillar_matches[0]["id"]
    detail_size = len(str(record.get("summary") or record.get("text") or record.get("body") or ""))
    long_first = primary_pillar in {"manual_task_automation", "tool_instructions", "use_cases_portfolio", "concepts_education"} or detail_size >= 700
    recommended_format = "long" if long_first else "short"
    return {
        "audiences": audience_matches[:2],
        "pillars": pillar_matches[:2],
        "recommended_format": recommended_format,
        "format_options": [recommended_format, "short" if recommended_format == "long" else "long"],
    }


def _parse_time(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)
    except ValueError:
        return None


def _engagement_score(record: dict) -> tuple[float | None, str]:
    explicit = record.get("engagement_score")
    if explicit is not None:
        try:
            return max(0.0, min(100.0, float(explicit))), "Normalized engagement supplied by the source adapter."
        except (TypeError, ValueError):
            pass
    values = {
        "views": record.get("view_count") or record.get("views"),
        "comments": record.get("comment_count") or record.get("comments"),
        "votes": record.get("score") or record.get("votes") or record.get("reactions"),
    }
    numeric: dict[str, float] = {}
    for name, value in values.items():
        try:
            if value is not None:
                numeric[name] = max(0.0, float(value))
        except (TypeError, ValueError):
            continue
    if not numeric:
        return None, "No comparable engagement metrics were available."
    score = 0.0
    if "views" in numeric:
        score += min(55.0, math.log1p(numeric["views"]) / math.log(1_000_001) * 55)
    if "comments" in numeric:
        score += min(25.0, math.log1p(numeric["comments"]) / math.log(10_001) * 25)
    if "votes" in numeric:
        score += min(20.0, math.log1p(numeric["votes"]) / math.log(10_001) * 20)
    return round(min(100.0, score), 2), "Normalized from available public view, comment, vote, or reaction counts."


def _offer_match(text: str, strategy: dict) -> tuple[float, list[str], str]:
    offers = []
    for lane in ("offers", "affiliates"):
        for item in strategy.get(lane, []) or []:
            if isinstance(item, dict) and item.get("enabled", True):
                offers.append((lane, item))
    matches = []
    affiliate_match = False
    for lane, offer in offers:
        keywords = [str(keyword).lower() for keyword in offer.get("keywords", [])]
        if any(keyword and keyword in text for keyword in keywords):
            matches.append(str(offer.get("name") or offer.get("id") or "configured offer"))
            affiliate_match = affiliate_match or lane == "affiliates"
    if not offers:
        return 0.0, [], "No active product, service, or affiliate profile is configured."
    if not matches:
        return 0.0, [], "The evidence does not match an active offer profile."
    base = min(100.0, 60.0 + max(0, len(matches) - 1) * 15.0)
    multiplier = float(strategy.get("scoring", {}).get("affiliate_match_multiplier", 1.5)) if affiliate_match else 1.0
    return round(min(100.0, base * multiplier), 2), matches, "Matched configured offer keywords; affiliate matches use the configured multiplier."


def _title_and_hook(record: dict, audience: dict, pillar: dict) -> tuple[str, str]:
    subject = re.sub(r"\s+", " ", str(record.get("title") or "This workflow")).strip()
    subject = subject[:110].rstrip(" .:-")
    audience_label = audience["label"]
    templates = {
        "news_updates": (f"{subject}: what changes for {audience_label}", "Lead with the verified change, then show one workflow implication and one unknown."),
        "tips_tricks": (f"A faster way to use {subject}", "Show the before state, the smallest useful shortcut, and the saved step."),
        "pain_point_solutions": (f"Fix this {audience_label} workflow problem: {subject}", "Open on the exact failure, reproduce it safely, then prove the fix."),
        "manual_task_automation": (f"Automate this manual workflow: {subject}", "Measure the manual path, build the automation, and compare the verified output."),
        "concepts_education": (f"{subject}, explained for {audience_label}", "Start with a familiar analogy, then connect it to one real decision."),
        "tool_instructions": (f"How to set up {subject}", "Show prerequisites first, then the shortest working path and a common failure."),
        "systems_mindset": (f"The system behind {subject}", "Turn the idea into a repeatable trigger, checklist, feedback loop, and stopping rule."),
        "use_cases_portfolio": (f"How I would prove {subject} works", "Frame the user problem, implementation, evidence, tradeoff, and next test."),
        "promotions_offers": (f"Who {subject} is actually for", "Teach the decision first; mention a relevant offer only after the evidence and fit are clear."),
        "comparisons_reviews": (f"{subject}: the evidence-based choice", "Compare the same job, constraints, cost, and verified result side by side."),
    }
    return templates[pillar["id"]]


def build_idea_queue(records: list[dict], strategy: dict | None = None, now: datetime | None = None) -> list[dict]:
    """Build a review queue without inventing missing trend, engagement, or trust evidence."""
    strategy = strategy or {}
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    weights = {**SCORING_WEIGHTS, **(strategy.get("scoring", {}) or {})}
    freshness_hours = int((strategy.get("research", {}) or {}).get("freshness_hours", 168))
    eligible_records = []
    for record in records:
        published = _parse_time(record.get("published") or record.get("scraped_at") or record.get("created_at"))
        is_research_signal = str(record.get("source_kind") or "article") != "article"
        if is_research_signal and published and now - published > timedelta(hours=freshness_hours):
            continue
        eligible_records.append(record)
    classified = [(record, classify_record(record)) for record in eligible_records]
    windows: Counter[tuple[str, str, str]] = Counter()
    prior: Counter[tuple[str, str, str]] = Counter()
    for record, labels in classified:
        published = _parse_time(record.get("published") or record.get("scraped_at") or record.get("created_at"))
        if not published:
            continue
        cluster = (labels["audiences"][0]["id"], labels["pillars"][0]["id"], str(record.get("source_kind") or record.get("source") or "unknown"))
        age = now - published
        if timedelta(0) <= age <= timedelta(hours=72):
            windows[cluster] += 1
        elif timedelta(hours=72) < age <= timedelta(hours=144):
            prior[cluster] += 1

    queue = []
    for record, labels in classified:
        audience = labels["audiences"][0]
        pillar = labels["pillars"][0]
        published = _parse_time(record.get("published") or record.get("scraped_at") or record.get("created_at"))
        cluster = (audience["id"], pillar["id"], str(record.get("source_kind") or record.get("source") or "unknown"))
        age = now - published if published else None
        if published and age is not None and timedelta(0) <= age <= timedelta(hours=72):
            current_count = windows[cluster]
            previous_count = prior[cluster]
            if previous_count:
                velocity = max(0.0, min(100.0, 50.0 + (current_count - previous_count) / previous_count * 50.0))
                velocity_basis = f"{current_count} matching signals in the latest 72h versus {previous_count} in the prior 72h."
            else:
                velocity = min(100.0, 30.0 + current_count * 15.0)
                velocity_basis = f"{current_count} matching signals in the latest 72h; no prior-window baseline."
        elif published:
            velocity = 0.0
            velocity_basis = "The signal is outside the latest 72-hour window; no current growth credit was assigned."
        else:
            velocity = None
            velocity_basis = "No parseable timestamp; 72-hour growth was not scored."

        engagement, engagement_basis = _engagement_score(record)
        monetization, offer_matches, monetization_basis = _offer_match(_record_text(record), strategy)
        components = {
            "keyword_growth_velocity": velocity,
            "source_engagement": engagement,
            "monetization_intent": monetization,
        }
        score = round(sum((components[name] or 0.0) * float(weights.get(name, SCORING_WEIGHTS[name])) for name in SCORING_WEIGHTS), 2)
        known_weight = sum(float(weights.get(name, SCORING_WEIGHTS[name])) for name, value in components.items() if value is not None)
        total_weight = sum(float(weights.get(name, SCORING_WEIGHTS[name])) for name in SCORING_WEIGHTS)
        evidence_coverage = round(known_weight / total_weight * 100) if total_weight else 0
        trust_value = record.get("source_trust_score")
        try:
            source_trust_score = float(trust_value) if trust_value is not None else None
        except (TypeError, ValueError):
            source_trust_score = None
        suggested_title, hook = _title_and_hook(record, audience, pillar)
        gaps = []
        if velocity is None:
            gaps.append("timestamp or 72-hour history")
        if engagement is None:
            gaps.append("comparable engagement")
        if source_trust_score is None:
            gaps.append("source trust review")
        if not str(record.get("summary") or record.get("text") or record.get("body") or "").strip():
            gaps.append("supporting excerpt")
        identity = str(record.get("url") or record.get("id") or suggested_title)
        queue.append({
            "id": hashlib.sha1(identity.encode("utf-8")).hexdigest()[:14],
            "suggested_title": suggested_title,
            "hook": hook,
            "audience": audience,
            "secondary_audiences": labels["audiences"][1:],
            "pillar": pillar,
            "secondary_pillars": labels["pillars"][1:],
            "recommended_format": labels["recommended_format"],
            "format_options": labels["format_options"],
            "content_velocity_score": score,
            "score_components": components,
            "score_basis": {
                "keyword_growth_velocity": velocity_basis,
                "source_engagement": engagement_basis,
                "monetization_intent": monetization_basis,
            },
            "evidence_coverage": evidence_coverage,
            "source_trust_score": source_trust_score,
            "source": str(record.get("source") or record.get("source_kind") or "Unknown"),
            "source_kind": str(record.get("source_kind") or "article"),
            "source_url": str(record.get("url") or ""),
            "source_title": str(record.get("title") or "Untitled"),
            "published": str(record.get("published") or record.get("scraped_at") or record.get("created_at") or ""),
            "offer_matches": offer_matches,
            "data_gaps": gaps,
            "review_status": "research_ready" if evidence_coverage >= 70 and source_trust_score is not None else "needs_review",
            "approval_required": True,
        })
    return sorted(queue, key=lambda row: (-row["content_velocity_score"], -row["evidence_coverage"], row["suggested_title"]))


def write_idea_exports(queue: list[dict], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "content_idea_queue.json"
    csv_path = output_dir / "content_idea_queue.csv"
    markdown_path = output_dir / "content_idea_queue.md"
    json_path.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = ["suggested_title", "audience", "pillar", "recommended_format", "content_velocity_score", "evidence_coverage", "review_status", "source", "source_url", "hook", "data_gaps"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in queue:
            writer.writerow({
                **{field: row.get(field, "") for field in fields},
                "audience": row["audience"]["label"],
                "pillar": row["pillar"]["label"],
                "data_gaps": "; ".join(row["data_gaps"]),
            })
    lines = ["# Content idea review queue", "", "> Scores rank available evidence; they do not predict virality, revenue, or monetization approval.", ""]
    for index, row in enumerate(queue, 1):
        lines.extend([
            f"## {index}. {row['suggested_title']}",
            "",
            f"- Audience: {row['audience']['label']}",
            f"- Pillar: {row['pillar']['label']}",
            f"- Formats: {row['recommended_format']} first; alternate {row['format_options'][1]}",
            f"- Evidence score: {row['content_velocity_score']}/100 with {row['evidence_coverage']}% component coverage",
            f"- Review: {row['review_status']} (human approval required)",
            f"- Hook: {row['hook']}",
            f"- Source: [{row['source']}]({row['source_url']})" if row["source_url"] else f"- Source: {row['source']}",
            f"- Data gaps: {', '.join(row['data_gaps']) or 'none recorded'}",
            "",
        ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "markdown": markdown_path}
