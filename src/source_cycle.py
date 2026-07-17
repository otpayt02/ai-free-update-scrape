"""Automatic source discovery, access rules, replacement, and archival."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml


# These are source-specific RSS endpoints, not search-result proxies. They are
# re-probed on every cycle; membership is never treated as permission to collect.
SOURCE_CATALOG = (
    {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml", "topics": ("foundation", "reasoning", "multimodal", "agents", "coding", "api")},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "topics": ("open-source", "models", "multimodal", "agents", "coding")},
    {"name": "GitHub AI and ML", "url": "https://github.blog/ai-and-ml/feed/", "topics": ("open-source", "coding", "developer", "agents")},
    {"name": "AWS Machine Learning Blog", "url": "https://aws.amazon.com/blogs/machine-learning/feed/", "topics": ("models", "developer", "api", "agents")},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "topics": ("foundation", "reasoning", "multimodal", "image", "video", "speech")},
    {"name": "NVIDIA Deep Learning", "url": "https://blogs.nvidia.com/blog/category/deep-learning/feed/", "topics": ("models", "multimodal", "image", "video", "speech")},
    {"name": "arXiv Computer Science AI", "url": "https://rss.arxiv.org/rss/cs.AI", "topics": ("foundation", "reasoning", "agents", "research")},
    {"name": "Hacker News AI", "url": "https://hnrss.org/newest?q=AI", "topics": ("developer", "open-source", "agents", "mcp", "coding")},
)

# Intent lanes are an operator-facing catalog. Only RSS candidates are
# automatically activated; APIs are linked as approved options to configure.
VIDEO_LANES = (
    {"id": "news_updates", "label": "News updates", "purpose": "New releases, research announcements, and platform changes.", "method": "Publisher RSS with a fresh access check on every cycle.", "restriction": "No search-result proxy or robots-restricted source is activated.", "sources": ("Hugging Face Blog", "GitHub AI and ML", "OpenAI News", "Google AI Blog", "NVIDIA Deep Learning")},
    {"id": "development_workflows", "label": "Development workflows", "purpose": "Engineering changes, implementation patterns, and tool adoption signals.", "method": "GitHub RSS plus the official GitHub Issues API when configured.", "restriction": "API use follows the provider's authentication, rate-limit, and terms requirements.", "sources": ("GitHub AI and ML", "Hacker News AI", "GitHub REST Issues API")},
    {"id": "tutorials", "label": "Tutorials", "purpose": "Teach a repeatable build, integration, or technical concept.", "method": "Publisher RSS and documented developer sources.", "restriction": "Each feed is re-probed before activation; article pages are not bypassed.", "sources": ("Hugging Face Blog", "AWS Machine Learning Blog", "GitHub AI and ML")},
    {"id": "pain_points", "label": "Pain-point research", "purpose": "Find recurring questions, failures, requests, and workflow friction.", "method": "Official community APIs and public feeds, collected with required credentials.", "restriction": "Reddit is official Data API only; direct scraping and access-control workarounds are excluded.", "sources": ("Hacker News AI", "Stack Exchange API", "Reddit Data API")},
    {"id": "website_design_problems", "label": "Website-design problems", "purpose": "Surface UX, accessibility, CSS, and implementation problems worth solving on video.", "method": "Official issue/community APIs and relevant publisher feeds.", "restriction": "Only policy-compliant API or feed collection is available in this lane.", "sources": ("Stack Exchange API", "GitHub REST Issues API", "Hacker News AI")},
)

API_CATALOG = {
    "GitHub REST Issues API": {"url": "https://docs.github.com/en/rest/issues/issues", "kind": "official API", "setup": "Configure an approved GitHub token when needed."},
    "Stack Exchange API": {"url": "https://api.stackexchange.com/docs", "kind": "official API", "setup": "Use the documented API key and OAuth flow when required."},
    "Reddit Data API": {"url": "https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki", "kind": "official API", "setup": "OAuth and Reddit developer terms are required; direct scraping is disabled."},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _audit_path(data: Path) -> Path:
    return data / "audit_queue.json"


def _append_audit(data: Path, entries: list[dict]) -> None:
    path = _audit_path(data)
    try:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except json.JSONDecodeError:
        existing = []
    _write_json(path, (existing + entries)[-1000:])


def _run_dir(data: Path, run_id: str) -> Path:
    path = data / "runs" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _matches_category(source: dict, category_name: str) -> bool:
    normalized = category_name.lower()
    return any(topic in normalized for topic in source["topics"])


def source_lane_catalog() -> list[dict]:
    """Return video-intent collection lanes without treating catalog membership as permission."""
    catalog_by_name = {source["name"]: source for source in SOURCE_CATALOG}
    lanes = []
    for lane in VIDEO_LANES:
        candidates = []
        for name in lane["sources"]:
            source = catalog_by_name.get(name)
            if source:
                candidates.append({"name": name, "url": source["url"], "kind": "RSS candidate", "setup": "Re-probed for HTTP, robots, content type, and parseability before activation."})
            else:
                candidates.append({"name": name, **API_CATALOG[name]})
        lanes.append({**lane, "candidates": candidates})
    return lanes


def discover_candidates(categories: list[dict], run_id: str) -> list[dict]:
    """Discover a diversified, source-specific RSS set matched to enabled topics."""
    enabled_names = [str(row.get("name", "AI updates")) for row in categories if row.get("enabled", True)]
    candidates = []
    for source in SOURCE_CATALOG:
        covered = [name for name in enabled_names if _matches_category(source, name)]
        if not covered:
            continue
        candidates.append({
            "source_id": f"{run_id[:8]}-{len(candidates) + 1:02d}",
            "name": source["name"],
            "url": source["url"],
            "type": "rss",
            "category": " | ".join(covered[:3]),
            "discovered_at": _now(),
            "origin": "curated source-specific RSS discovery",
        })
    return candidates


def _is_restricted_robots(text: str) -> bool:
    lowered = text.lower()
    return "user-agent: *" in lowered and "disallow: /" in lowered


def plan_candidate(candidate: dict) -> dict:
    """Probe one candidate and return a source rule without bypassing access controls."""
    url = candidate["url"]
    parsed = urlparse(url)
    rule = {
        **candidate,
        "checked_at": _now(),
        "status": "rejected",
        "http_status": None,
        "robots": "unknown",
        "content_type": "",
        "allowed_cadence": "once per scrape run",
        "parser": "feedparser RSS/Atom",
        "selector_notes": "Feed entries: title, link, summary, and published timestamp.",
        "instruction": "Fetch the RSS/Atom feed once, parse entries, canonicalize URLs, and record parse yield.",
        "reason": "",
    }
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True, headers={"User-Agent": "ai-free-update-scrape/1.0 (+local operator console)"})
        rule["http_status"] = response.status_code
        rule["content_type"] = response.headers.get("content-type", "")
        if response.status_code in (401, 403, 429):
            rule["reason"] = f"Rejected: HTTP {response.status_code} blocks or rate-limits collection."
            return rule
        response.raise_for_status()
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            robots = httpx.get(robots_url, timeout=8, headers={"User-Agent": "ai-free-update-scrape/1.0"}).text[:20000]
            rule["robots"] = "restricted" if _is_restricted_robots(robots) else "reviewed"
        except httpx.HTTPError:
            rule["robots"] = "unavailable"
        if rule["robots"] == "restricted":
            rule["reason"] = "Rejected: robots.txt disallows site-wide collection."
            return rule
        content = response.text[:2000].lower()
        if "rss" not in rule["content_type"].lower() and "xml" not in rule["content_type"].lower() and "<rss" not in content and "<feed" not in content:
            rule["reason"] = "Rejected: no supported RSS/Atom or named parser was detected."
            return rule
        rule["status"] = "ready"
        rule["reason"] = "Ready: parseable feed passed access, robots, and content checks."
    except httpx.HTTPError as exc:
        rule["reason"] = f"Rejected: request failed ({str(exc)[:180]})."
    return rule


def replace_sources(sources_path: Path, ready_rules: list[dict]) -> dict:
    """Replace active sources only with current ready rules."""
    payload = {"rss": [], "scrape": []}
    for rule in ready_rules:
        source = {key: rule[key] for key in ("name", "url", "type")}
        source["enabled"] = True
        source["source_id"] = rule["source_id"]
        source["category"] = rule["category"]
        payload["rss"].append(source)
    sources_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return payload


def run_source_cycle(data: Path, sources_path: Path, categories: list[dict], run_id: str) -> dict:
    """Discover, vet, archive, audit, and atomically replace active sources."""
    folder = _run_dir(data, run_id)
    candidates = discover_candidates(categories, run_id)
    rules = [plan_candidate(candidate) for candidate in candidates]
    ready = [rule for rule in rules if rule["status"] == "ready"]
    audit = [{
        "id": f"{run_id}:{rule['source_id']}", "run_id": run_id, "source_id": rule["source_id"],
        "source": rule["name"], "url": rule["url"], "status": rule["status"],
        "reason": rule["reason"], "retry": rule["status"] != "ready", "created_at": _now(),
        "archive": str(folder.relative_to(data)),
    } for rule in rules]
    _write_json(folder / "source_candidates.json", candidates)
    _write_json(folder / "source_rules.json", rules)
    _append_audit(data, audit)
    if not ready:
        _write_json(folder / "manifest.json", {"run_id": run_id, "status": "blocked", "reason": "No source passed the automatic access rules.", "created_at": _now()})
        return {"ok": False, "run_id": run_id, "rules": rules, "ready": 0, "reason": "No source passed access, robots, and parser checks."}
    active = replace_sources(sources_path, ready)
    _write_json(folder / "active_sources.json", active)
    _write_json(folder / "manifest.json", {"run_id": run_id, "status": "ready", "ready_sources": len(ready), "created_at": _now()})
    return {"ok": True, "run_id": run_id, "rules": rules, "ready": len(ready), "active_sources": active}


def archive_outputs(data: Path, run_id: str) -> list[str]:
    """Copy the current outputs into the same source-cycle archive after a successful run."""
    folder = _run_dir(data, run_id)
    copied = []
    for source in (data / "digests", data / "exports", data / "processed" / "processed_articles.jsonl", data / "ledger.jsonl"):
        if not source.exists():
            continue
        target = folder / source.name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
        copied.append(target.name)
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"run_id": run_id}
    manifest.update({"status": "archived", "outputs": copied, "archived_at": _now()})
    _write_json(manifest_path, manifest)
    return copied


def list_runs(data: Path) -> list[dict]:
    root = data / "runs"
    if not root.exists():
        return []
    rows = []
    for folder in sorted((path for path in root.iterdir() if path.is_dir()), reverse=True):
        manifest = folder / "manifest.json"
        if manifest.exists():
            try:
                rows.append(json.loads(manifest.read_text(encoding="utf-8")) | {"id": folder.name})
            except json.JSONDecodeError:
                pass
    return rows
