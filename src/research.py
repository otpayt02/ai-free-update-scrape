"""Official-API research collectors and review-gated source discovery."""

from __future__ import annotations

import csv
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml


USER_AGENT = "ai-free-update-scrape/1.0 (+local evidence research; contact: operator)"

COLLECTOR_CATALOG = (
    {"id": "stackexchange", "label": "Stack Exchange questions", "access": "official API", "pain_signal": "unanswered, high-view, or highly voted technical questions", "restriction": "Public question fields only; no author profiling."},
    {"id": "github", "label": "GitHub issues", "access": "official REST API", "pain_signal": "open bugs, documentation gaps, feature requests, and integration failures", "restriction": "Public issues only; pull requests and author identities are not retained."},
    {"id": "youtube", "label": "YouTube comments", "access": "YouTube Data API", "pain_signal": "questions, failed steps, missing use cases, and requested follow-ups", "restriction": "Requires YOUTUBE_API_KEY; author identities are not retained."},
    {"id": "reddit", "label": "Reddit communities", "access": "Reddit Data API", "pain_signal": "workflow questions and recurring frustrations by community", "restriction": "Requires approved OAuth access; direct page scraping is disabled."},
    {"id": "review_import", "label": "Approved review exports", "access": "local CSV or JSONL import", "pain_signal": "low-rated product feedback supplied by the operator", "restriction": "No stealth browser collection from review sites; import only an export you are allowed to use."},
)

SOURCE_TRUST_CRITERIA = (
    {"id": "permitted_access", "weight": 20, "question": "Is collection explicitly allowed through an official API, RSS feed, export, or written permission?"},
    {"id": "publisher_identity", "weight": 15, "question": "Can the publisher, author, or accountable organization be identified?"},
    {"id": "primary_evidence", "weight": 15, "question": "Does the source link to primary documents, data, code, or direct statements?"},
    {"id": "freshness", "weight": 15, "question": "Is the relevant material current enough for the claim being made?"},
    {"id": "corroboration", "weight": 15, "question": "Can material claims be corroborated independently?"},
    {"id": "corrections_transparency", "weight": 10, "question": "Are corrections, dates, conflicts, and updates visible?"},
    {"id": "security", "weight": 5, "question": "Does the source use HTTPS?"},
    {"id": "commercial_disclosure", "weight": 5, "question": "Are sponsorships, affiliate relationships, and commercial incentives disclosed?"},
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_research_config(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    return payload if isinstance(payload, dict) else {}


def _clean_html(value: object) -> str:
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html.unescape(str(value or "")))).strip()


def _append_jsonl(path: Path, records: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                existing.add(str(row.get("url") or row.get("id") or row.get("title")))
            except json.JSONDecodeError:
                continue
    added = 0
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            identity = str(record.get("url") or record.get("id") or record.get("title"))
            if not identity or identity in existing:
                continue
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            existing.add(identity)
            added += 1
    return added


class ResearchCollector:
    """Small, bounded collectors that retain evidence text but not author identities."""

    def __init__(self, client: httpx.Client | None = None, limit: int = 25, freshness_hours: int = 168):
        self.client = client or httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT})
        self.limit = max(1, min(int(limit), 100))
        self.freshness_hours = max(1, min(int(freshness_hours), 8760))

    def stackexchange(self, tags: list[str]) -> list[dict]:
        rows = []
        cutoff = int(datetime.now(timezone.utc).timestamp()) - self.freshness_hours * 3600
        for tag in tags[:8]:
            response = self.client.get("https://api.stackexchange.com/2.3/questions", params={"site": "stackoverflow", "tagged": tag, "fromdate": cutoff, "sort": "activity", "order": "desc", "pagesize": self.limit, "filter": "withbody"})
            response.raise_for_status()
            for item in response.json().get("items", []):
                rows.append({
                    "id": f"stackexchange:{item.get('question_id')}", "title": _clean_html(item.get("title")),
                    "text": _clean_html(item.get("body")), "url": item.get("link", ""), "source": f"Stack Overflow / {tag}",
                    "source_kind": "stackexchange_question", "published": datetime.fromtimestamp(item.get("creation_date", 0), tz=timezone.utc).isoformat(),
                    "view_count": item.get("view_count", 0), "comment_count": item.get("answer_count", 0), "score": item.get("score", 0),
                    "pain_signal": item.get("answer_count", 0) == 0, "collected_at": _now(),
                })
        return rows[: self.limit]

    def github(self, repositories: list[str]) -> list[dict]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        rows = []
        cutoff = datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() - self.freshness_hours * 3600, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        for repository in repositories[:10]:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
                continue
            response = self.client.get(f"https://api.github.com/repos/{repository}/issues", params={"state": "open", "sort": "updated", "direction": "desc", "since": cutoff, "per_page": self.limit}, headers=headers)
            response.raise_for_status()
            for item in response.json():
                if "pull_request" in item:
                    continue
                rows.append({
                    "id": f"github:{repository}:{item.get('number')}", "title": item.get("title", ""), "text": item.get("body") or "",
                    "url": item.get("html_url", ""), "source": repository, "source_kind": "github_issue", "published": item.get("updated_at", ""), "created_at": item.get("created_at", ""),
                    "comment_count": item.get("comments", 0), "pain_signal": True, "labels": [label.get("name", "") for label in item.get("labels", [])], "collected_at": _now(),
                })
        return rows[: self.limit]

    def youtube(self, video_ids: list[str], key_env: str) -> list[dict]:
        api_key = os.getenv(key_env, "").strip()
        if not api_key:
            raise RuntimeError(f"{key_env} is not configured")
        rows = []
        for video_id in video_ids[:20]:
            response = self.client.get("https://www.googleapis.com/youtube/v3/commentThreads", params={"part": "snippet", "videoId": video_id, "maxResults": min(100, self.limit), "textFormat": "plainText", "key": api_key})
            response.raise_for_status()
            for item in response.json().get("items", []):
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                rows.append({
                    "id": f"youtube:{item.get('id')}", "title": f"YouTube comment on {video_id}", "text": snippet.get("textDisplay", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}&lc={item.get('id', '')}", "source": "YouTube Data API", "source_kind": "youtube_comment",
                    "published": snippet.get("publishedAt", ""), "votes": snippet.get("likeCount", 0), "pain_signal": True, "collected_at": _now(),
                })
        return rows[: self.limit]

    def reddit(self, communities: list[str], token_env: str) -> list[dict]:
        token = os.getenv(token_env, "").strip()
        if not token:
            raise RuntimeError(f"{token_env} is not configured")
        rows = []
        headers = {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}
        for community in communities[:10]:
            response = self.client.get(f"https://oauth.reddit.com/r/{community}/new", params={"limit": self.limit}, headers=headers)
            response.raise_for_status()
            for child in response.json().get("data", {}).get("children", []):
                item = child.get("data", {})
                rows.append({
                    "id": f"reddit:{item.get('id')}", "title": item.get("title", ""), "text": item.get("selftext", ""),
                    "url": f"https://www.reddit.com{item.get('permalink', '')}", "source": f"r/{community}", "source_kind": "reddit_post",
                    "published": datetime.fromtimestamp(item.get("created_utc", 0), tz=timezone.utc).isoformat(),
                    "comment_count": item.get("num_comments", 0), "votes": item.get("score", 0), "pain_signal": True, "collected_at": _now(),
                })
        return rows[: self.limit]

    def review_import(self, paths: list[str], import_root: Path) -> list[dict]:
        rows = []
        root = import_root.resolve()
        for configured in paths[:20]:
            path = (root / configured).resolve()
            if root not in path.parents or not path.exists() or path.suffix.lower() not in {".csv", ".jsonl"}:
                continue
            if path.suffix.lower() == ".csv":
                with path.open(encoding="utf-8", newline="") as handle:
                    imported = list(csv.DictReader(handle))
            else:
                imported = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            for index, item in enumerate(imported):
                rating = item.get("rating")
                if rating not in (None, ""):
                    try:
                        if float(rating) > 3:
                            continue
                    except (TypeError, ValueError):
                        pass
                rows.append({
                    "id": f"review-import:{path.name}:{index}", "title": str(item.get("title") or item.get("product") or "Imported product review"),
                    "text": str(item.get("text") or item.get("review") or item.get("body") or ""), "url": str(item.get("url") or ""),
                    "source": str(item.get("source") or path.name), "source_kind": "approved_review_import", "published": str(item.get("published") or ""),
                    "rating": rating, "pain_signal": True, "collected_at": _now(),
                })
        return rows[: self.limit]


def collect_research_signals(config_path: Path, output_path: Path, import_root: Path, client: httpx.Client | None = None) -> dict:
    config = load_research_config(config_path)
    research = config.get("research", {}) or {}
    settings = research.get("collectors", {}) or {}
    collector = ResearchCollector(client=client, limit=int(research.get("max_items_per_collector", 25)), freshness_hours=int(research.get("freshness_hours", 168)))
    records = []
    statuses = []
    for metadata in COLLECTOR_CATALOG:
        collector_id = metadata["id"]
        entry = settings.get(collector_id, {}) or {}
        if not entry.get("enabled", False):
            statuses.append({"id": collector_id, "status": "disabled", "collected": 0, "message": metadata["restriction"]})
            continue
        try:
            if collector_id == "stackexchange":
                found = collector.stackexchange(list(entry.get("tags", [])))
            elif collector_id == "github":
                found = collector.github(list(entry.get("repositories", [])))
            elif collector_id == "youtube":
                found = collector.youtube(list(entry.get("video_ids", [])), str(entry.get("key_env", "YOUTUBE_API_KEY")))
            elif collector_id == "reddit":
                found = collector.reddit(list(entry.get("communities", [])), str(entry.get("token_env", "REDDIT_ACCESS_TOKEN")))
            else:
                found = collector.review_import(list(entry.get("paths", [])), import_root)
            records.extend(found)
            statuses.append({"id": collector_id, "status": "ok", "collected": len(found), "message": metadata["access"]})
        except (httpx.HTTPError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            statuses.append({"id": collector_id, "status": "blocked", "collected": 0, "message": str(exc)[:240]})
    added = _append_jsonl(output_path, records)
    return {"ok": any(row["status"] == "ok" for row in statuses), "collected": len(records), "added": added, "collectors": statuses, "output": str(output_path)}


def _load_registry(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except (json.JSONDecodeError, OSError):
        return []


DEFAULT_DISCOVERY_KEYWORDS = (
    "ai", "artificial intelligence", "machine learning", "llm", "model", "agent", "automation",
    "python", "developer", "programming", "code", "software", "open source", "github", "api",
    "cloud", "aws", "database", "data", "security", "robot", "browser", "web", "mobile", "hardware",
)
PRIMARY_DISCOVERY_KEYWORDS = {
    "ai", "artificial intelligence", "machine learning", "llm", "model", "agent", "automation", "python", "robot",
}


def _discovery_matches(story: dict, keywords: tuple[str, ...]) -> list[str]:
    text = " ".join(str(story.get(field) or "") for field in ("title", "text")).lower()
    return sorted({
        keyword
        for keyword in keywords
        if re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text)
    })


def _discovery_is_relevant(matches: list[str]) -> bool:
    return bool(PRIMARY_DISCOVERY_KEYWORDS.intersection(matches)) or len(matches) >= 2


def discover_source_candidates(config_path: Path, registry_path: Path, client: httpx.Client | None = None) -> dict:
    """Persist relevant novel HN-linked domains as review candidates; never auto-activate them."""
    config = load_research_config(config_path)
    settings = config.get("source_discovery", {}) or {}
    if not settings.get("enabled", True):
        return {"ok": False, "added": 0, "reason": "Source discovery is disabled.", "registry": _load_registry(registry_path)}
    client = client or httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    limit = max(1, min(int(settings.get("hacker_news_story_limit", 25)), 50))
    configured_keywords = settings.get("relevance_keywords", DEFAULT_DISCOVERY_KEYWORDS)
    relevance_keywords = tuple(str(keyword).strip().lower() for keyword in configured_keywords if str(keyword).strip())
    story_ids = client.get("https://hacker-news.firebaseio.com/v0/newstories.json").raise_for_status().json()[:limit]
    candidates = []
    for story_id in story_ids:
        response = client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        response.raise_for_status()
        story = response.json() or {}
        matched_keywords = _discovery_matches(story, relevance_keywords)
        if not _discovery_is_relevant(matched_keywords):
            continue
        url = str(story.get("url") or "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            continue
        domain = parsed.hostname.lower().removeprefix("www.")
        candidates.append({
            "domain": domain, "sample_url": url, "sample_title": str(story.get("title") or ""),
            "discovered_at": _now(), "discovery_origin": "Hacker News official Firebase API",
            "relevance_keywords": matched_keywords,
            "status": "review_required", "trust_score": 5,
            "trust_dimensions": {"security": 5},
            "missing_review": [criterion["id"] for criterion in SOURCE_TRUST_CRITERIA if criterion["id"] != "security"],
            "activation_allowed": False,
            "next_action": "Find a permitted RSS/API route, verify publisher identity and primary evidence, then complete human trust review.",
        })
    existing_registry = _load_registry(registry_path)
    existing = [
        row for row in existing_registry
        if row.get("discovery_origin") != "Hacker News official Firebase API"
        or row.get("activation_allowed", False)
        or _discovery_is_relevant(_discovery_matches({"title": row.get("sample_title")}, relevance_keywords))
    ]
    removed_out_of_scope = len(existing_registry) - len(existing)
    by_domain = {row.get("domain"): row for row in existing if row.get("domain")}
    added = 0
    for candidate in candidates:
        if candidate["domain"] not in by_domain:
            by_domain[candidate["domain"]] = candidate
            added += 1
        elif by_domain[candidate["domain"]].get("status") == "review_required" and not by_domain[candidate["domain"]].get("activation_allowed", False):
            prior = by_domain[candidate["domain"]]
            candidate["discovered_at"] = prior.get("discovered_at", candidate["discovered_at"])
            candidate["last_seen_at"] = _now()
            by_domain[candidate["domain"]] = candidate
    for record in by_domain.values():
        if record.get("status") == "review_required" and not record.get("activation_allowed", False):
            record["trust_score"] = 5
            record["trust_dimensions"] = {"security": 5}
            record["missing_review"] = [criterion["id"] for criterion in SOURCE_TRUST_CRITERIA if criterion["id"] != "security"]
    registry = sorted(by_domain.values(), key=lambda row: (row.get("status", ""), row.get("domain", "")))
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "added": added,
        "discovered": len(candidates),
        "removed_out_of_scope": removed_out_of_scope,
        "registry": registry,
        "activation_requires_human_review": True,
    }


def source_registry_payload(path: Path) -> dict:
    return {"sources": _load_registry(path), "trust_criteria": list(SOURCE_TRUST_CRITERIA), "activation_requires_human_review": True}
