"""Three-stage discovery, access-planning, and run-artifact workflow."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import feedparser
import httpx


def _run_dir(data: Path, stage: int) -> Path:
    root = data / "runs"
    root.mkdir(parents=True, exist_ok=True)
    sequence = len([path for path in root.iterdir() if path.is_dir()]) + 1
    path = root / f"scrape-{sequence:04d}-stage-{stage}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def discover_sources(data: Path, categories: list[dict], per_category: int, max_sources: int) -> dict:
    """Discover current candidate domains through Bing News RSS queries."""
    run_dir = _run_dir(data, 1)
    candidates: list[dict] = []
    seen: set[str] = set()
    for category in [item for item in categories if item.get("enabled", True)]:
        query = quote(f'{category["name"]} AI when:1d')
        feed = feedparser.parse(f"https://www.bing.com/news/search?q={query}&format=rss")
        found = 0
        for entry in feed.entries:
            link = entry.get("link", "")
            wrapped = parse_qs(urlparse(link).query).get("url", [])
            if wrapped:
                link = unquote(wrapped[0])
            domain = urlparse(link).netloc.lower().removeprefix("www.")
            if not domain or domain in seen:
                continue
            seen.add(domain)
            candidates.append({"id": uuid.uuid4().hex[:10], "name": domain, "url": link, "domain": domain, "category": category["name"], "headline": entry.get("title", ""), "status": "candidate", "selected": True})
            found += 1
            if found >= per_category or len(candidates) >= max_sources:
                break
        if len(candidates) >= max_sources:
            break
    payload = {"stage": 1, "created_at": datetime.now().isoformat(), "run_id": run_dir.name, "candidates": candidates}
    (run_dir / "source_candidates.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def plan_sources(data: Path, sources: list[dict], tips_per_source: int = 5) -> dict:
    """Probe source access constraints and produce bounded collection guidance."""
    run_dir = _run_dir(data, 2)
    plans = []
    for source in sources:
        base = f'{urlparse(source["url"]).scheme}://{urlparse(source["url"]).netloc}'
        plan = {"source": source.get("name") or source.get("domain"), "url": source["url"], "status": "ready", "http_status": None, "robots": "unknown", "tips": []}
        try:
            response = httpx.get(source["url"], follow_redirects=True, timeout=12, headers={"User-Agent": "Mozilla/5.0 ai-free-update-scrape/1.0"})
            plan["http_status"] = response.status_code
            content = response.text.lower()
            if response.status_code in (401, 403, 429) or "captcha" in content or "cloudflare" in content:
                plan["status"] = "blocked"
                plan["tips"].append("Prefer an official RSS feed or API; do not bypass access controls.")
            robots = httpx.get(f"{base}/robots.txt", timeout=8).text[:20000]
            plan["robots"] = "restricted" if re.search(r"disallow:\s*/\s*$", robots, re.I | re.M) else "reviewed"
            content_type = response.headers.get("content-type", "")
            plan["tips"].extend([
                f"Use the returned {content_type.split(';')[0] or 'document'} format.",
                "Cache URLs and content hashes before parsing.",
                "Respect robots.txt, rate limits, and retry-after headers.",
                "Canonicalize URLs before cross-source deduplication.",
                "Record status, latency, bytes, and parse yield for every request.",
            ])
        except Exception as exc:
            plan.update(status="unreachable", error=str(exc)[:180])
            plan["tips"] = ["Skip this source for this run and replace it with another candidate."]
        plan["tips"] = plan["tips"][:tips_per_source]
        plans.append(plan)
    payload = {"stage": 2, "created_at": datetime.now().isoformat(), "run_id": run_dir.name, "plans": plans}
    (run_dir / "source_plans.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def archive_production_run(data: Path) -> dict:
    """Copy current production deliverables into one inspectable run folder."""
    run_dir = _run_dir(data, 3)
    copied = []
    for source in [data / "digests", data / "exports", data / "processed" / "processed_articles.jsonl", data / "ledger.jsonl"]:
        if not source.exists():
            continue
        target = run_dir / source.name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
        copied.append(target.name)
    manifest = {"stage": 3, "created_at": datetime.now().isoformat(), "run_id": run_dir.name, "artifacts": copied}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def list_runs(data: Path) -> list[dict]:
    """List run folders and their downloadable files."""
    root = data / "runs"
    if not root.exists():
        return []
    rows = []
    for folder in sorted((path for path in root.iterdir() if path.is_dir()), reverse=True):
        files = [{"name": str(path.relative_to(folder)), "size": path.stat().st_size} for path in folder.rglob("*") if path.is_file()]
        rows.append({"id": folder.name, "files": files, "count": len(files)})
    return rows
