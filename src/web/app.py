"""Local control center for configuring, running, and observing the scraper."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import threading
import time
import uuid
from html import unescape
from re import sub
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import httpx
import yaml
from flask import Flask, jsonify, request, send_from_directory

from ..categories import load_categories, save_categories
from ..content_intelligence import AUDIENCE_TAXONOMY, CONTENT_PILLARS, build_idea_queue, load_strategy, write_idea_exports
from ..providers import (
    PROVIDERS,
    credential_status,
    credential_statuses,
    discover_local_models,
    discover_models,
    save_user_credential,
    test_model,
)
from ..session import DEFAULT_SESSION, SessionProfile, select_session_items
from ..telemetry import TelemetryStore
from ..source_cycle import archive_outputs, list_runs, run_source_cycle, source_lane_catalog
from ..research import COLLECTOR_CATALOG, collect_research_signals, discover_source_candidates, source_registry_payload
from ..yt_auto_mcp import TOOLS as YT_AUTO_TOOLS
from ..yt_auto_mcp import call_tool as call_yt_auto_tool
from ..yt_auto_mcp import handle_jsonrpc as handle_yt_auto_jsonrpc
from ..yt_auto_mcp import status as yt_auto_status


BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
CONFIG = BASE / "config"
DASHBOARD_CONFIG = CONFIG / "dashboard.json"
SOURCES_CONFIG = CONFIG / "sources.yaml"
CATEGORIES_CONFIG = CONFIG / "categories.json"
TELEMETRY_PATH = DATA / "telemetry" / "events.jsonl"
WORKSPACE_PATH = DATA / "workspace.json"
CONTENT_STRATEGY = CONFIG / "content_strategy.yaml"
RESEARCH_SIGNALS = DATA / "research" / "signals.jsonl"
SOURCE_REGISTRY = DATA / "source_registry.json"
FRONTEND_DIST = BASE / "frontend" / "dist"

CONFIG_FIELDS = {
    "ai_industry_items": (1, 100),
    "free_items": (0, 100),
    "max_items_per_run": (1, 500),
    "rss_limit": (1, 100),
    "hn_limit": (1, 500),
    "web_limit": (1, 100),
    "plan_days": (1, 365),
    "plan_per_day": (1, 20),
}


def _default_config() -> dict:
    profile = DEFAULT_SESSION.as_dict()
    return {
        **{key: profile[key] for key in CONFIG_FIELDS},
        "llm_model": profile["llm_model"], "skip_llm": False,
        "request_timeout_seconds": 20, "retry_limit": 3, "retry_backoff_seconds": 2,
        "global_concurrency": 6, "per_domain_concurrency": 2, "requests_per_minute": 60,
        "freshness_hours": 72, "duplicate_threshold": 0.92, "retention_days": 90,
        "timezone": "America/New_York", "refresh_seconds": 5, "log_level": "INFO",
        "selected_provider": "nvidia", "selected_model": "",
        "nvidia_model": "", "nvidia_temperature": 0.7, "nvidia_top_p": 0.95,
        "nvidia_max_tokens": 4096, "nvidia_thinking": False, "nvidia_stream": False,
    }


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except (json.JSONDecodeError, TypeError):
            continue
    return rows


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_workspace() -> dict:
    """Load the operator journal and reusable content templates."""
    default = {"journal": [], "templates": []}
    if not WORKSPACE_PATH.exists():
        return default
    try:
        payload = json.loads(WORKSPACE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        return default
    return {
        "journal": payload.get("journal", []) if isinstance(payload.get("journal", []), list) else [],
        "templates": payload.get("templates", []) if isinstance(payload.get("templates", []), list) else [],
    }


def _save_workspace(payload: dict) -> None:
    WORKSPACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKSPACE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_audit() -> list[dict]:
    path = DATA / "audit_queue.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except json.JSONDecodeError:
        return []


def _portfolio_scores(articles: list[dict]) -> list[dict]:
    """Derive inspectable 0-100 portfolio fit from stored article evidence."""
    rows = []
    for article in articles:
        ranking = article.get("ranking", {})
        relevance = min(100, round(float(ranking.get("top_score", 0) or 0) * 10))
        topics = article.get("topics") or article.get("categories") or []
        business = min(100, round(relevance * .75 + sum(8 for topic in topics if topic in {"product", "agents", "free"})))
        reuse = min(100, round(len(topics) * 12 + min(48, len(str(article.get("summary", ""))) / 12) + (12 if article.get("alternatives") else 0)))
        technical = min(100, sum({"models": 28, "agents": 24, "builders": 26, "product": 12, "free": 10}.get(topic, 6) for topic in topics) + (10 if article.get("detection", {}).get("new_tool") else 0))
        proof = min(100, 15 + (25 if article.get("url") else 0) + (20 if article.get("published") else 0) + min(30, len(str(article.get("summary", ""))) / 20) + (10 if article.get("source") else 0))
        scraped = str(article.get("scraped_at") or article.get("published") or "")
        try:
            published = datetime.fromisoformat(scraped.replace("Z", "+00:00"))
            age_hours = max(0, (datetime.now(published.tzinfo) - published).total_seconds() / 3600)
            current = max(0, round(relevance - age_hours / 10))
        except ValueError:
            current = relevance
        total = round(business * .25 + reuse * .20 + technical * .20 + proof * .20 + current * .15)
        rows.append({"title": article.get("title", "Untitled"), "url": article.get("url", ""), "source": article.get("source", "Unknown"), "score": total, "metrics": {"business": business, "reuse": reuse, "technical": technical, "proof": proof, "relevance": current}, "reason": ranking.get("reason") or f"Evidence: {len(topics)} topic tags, source fields, content depth, and current scrape time."})
    return sorted(rows, key=lambda row: row["score"], reverse=True)[:20]


def _load_config() -> dict:
    config = _default_config()
    if DASHBOARD_CONFIG.exists():
        try:
            config.update(json.loads(DASHBOARD_CONFIG.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, TypeError):
            pass
    if "phi4" in str(config.get("llm_model", "")).lower():
        config["llm_model"] = ""
    return config


def _validate_config(payload: dict) -> tuple[dict, list[str]]:
    clean = _default_config()
    errors: list[str] = []
    for field, (minimum, maximum) in CONFIG_FIELDS.items():
        try:
            value = int(payload.get(field, clean[field]))
        except (TypeError, ValueError):
            errors.append(f"{field} must be a whole number")
            continue
        if not minimum <= value <= maximum:
            errors.append(f"{field} must be between {minimum} and {maximum}")
        clean[field] = value
    clean["skip_llm"] = bool(payload.get("skip_llm", False))
    clean["llm_model"] = str(payload.get("llm_model", clean["llm_model"])).strip()
    if clean["ai_industry_items"] + clean["free_items"] > clean["max_items_per_run"]:
        errors.append("Industry and free targets cannot exceed the maximum items per run")
    for field, bounds in {
        "request_timeout_seconds": (1, 300), "retry_limit": (0, 10), "retry_backoff_seconds": (0, 60),
        "global_concurrency": (1, 64), "per_domain_concurrency": (1, 16), "requests_per_minute": (1, 1000),
        "freshness_hours": (1, 8760), "retention_days": (1, 3650), "refresh_seconds": (1, 300),
        "nvidia_max_tokens": (1, 32768),
    }.items():
        try:
            clean[field] = int(payload.get(field, clean[field]))
            if not bounds[0] <= clean[field] <= bounds[1]:
                errors.append(f"{field} must be between {bounds[0]} and {bounds[1]}")
        except (TypeError, ValueError):
            errors.append(f"{field} must be a whole number")
    for field in ("duplicate_threshold", "nvidia_temperature", "nvidia_top_p"):
        try:
            clean[field] = float(payload.get(field, clean[field]))
        except (TypeError, ValueError):
            errors.append(f"{field} must be numeric")
    for field in ("timezone", "log_level", "nvidia_model"):
        clean[field] = str(payload.get(field, clean[field])).strip()
    clean["nvidia_thinking"] = bool(payload.get("nvidia_thinking", clean["nvidia_thinking"]))
    clean["nvidia_stream"] = bool(payload.get("nvidia_stream", clean["nvidia_stream"]))
    clean["selected_provider"] = str(payload.get("selected_provider", clean["selected_provider"])).strip()
    clean["selected_model"] = str(payload.get("selected_model", clean["selected_model"])).strip()
    return clean, errors


def _load_sources() -> dict:
    if not SOURCES_CONFIG.exists():
        return {"rss": [], "scrape": []}
    return yaml.safe_load(SOURCES_CONFIG.read_text(encoding="utf-8")) or {"rss": [], "scrape": []}


def _profile_from_config(config: dict) -> SessionProfile:
    return SessionProfile(
        min_items=config["ai_industry_items"] + config["free_items"],
        ai_industry_items=config["ai_industry_items"],
        free_items=config["free_items"],
        max_items_per_run=config["max_items_per_run"],
        rss_limit=config["rss_limit"],
        hn_limit=config["hn_limit"],
        web_limit=config["web_limit"],
        plan_days=config["plan_days"],
        plan_per_day=config["plan_per_day"],
    )


def build_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    telemetry = TelemetryStore(TELEMETRY_PATH)
    run_state = {"status": "idle", "run_id": None, "started_at": None, "finished_at": None, "exit_code": None, "log": deque(maxlen=300), "process": None}
    run_lock = threading.Lock()

    def snapshot() -> dict:
        articles = _read_jsonl(DATA / "processed" / "processed_articles.jsonl")
        shorts = _read_csv(DATA / "exports" / "shorts_plan.csv")
        config = _load_config()
        selected = select_session_items(articles, _profile_from_config(config))
        source_counts = Counter(article.get("source", "Unknown") for article in articles)
        topic_counts = Counter(topic for article in articles for topic in article.get("topics", []))
        configured_sources = sum(
            1 for group in view_sources.values() for source in group if source.get("enabled", True)
        ) if (view_sources := _load_sources()) else 0
        return {
            "articles": articles,
            "shorts": shorts,
            "selected": selected,
            "config": config,
            "sources": view_sources,
            "source_counts": source_counts,
            "topic_counts": topic_counts,
            "stats": {
                "articles": len(articles),
                "session_articles": len(selected["selected"]),
                "shorts": len(shorts),
                "sources": configured_sources,
                "runs": len(_read_jsonl(DATA / "ledger.jsonl")),
            },
        }

    def execute_run(config: dict) -> None:
        run_id = str(uuid.uuid4())
        command = [
            sys.executable, str(BASE / "run.py"),
            "--plan-days", str(config["plan_days"]),
            "--plan-per-day", str(config["plan_per_day"]),
            "--rss-limit", str(config["rss_limit"]),
            "--hn-limit", str(config["hn_limit"]),
            "--web-limit", str(config["web_limit"]),
            "--industry-target", str(config["ai_industry_items"]),
            "--free-target", str(config["free_items"]),
            "--max-items", str(config["max_items_per_run"]),
            "--llm-model", str(config.get("selected_model") or config.get("nvidia_model") or config.get("llm_model") or ""),
            "--provider", str(config.get("selected_provider") or "nvidia"),
        ]
        if config["skip_llm"]:
            command.append("--skip-llm")
        with run_lock:
            run_state.update(status="running", run_id=run_id, started_at=datetime.now().isoformat(timespec="seconds"), finished_at=None, exit_code=None)
            run_state["log"].clear()
        telemetry.emit(run_id, "configuration_resolution", "ok", config_snapshot={key: value for key, value in config.items() if "key" not in key.lower()})
        cycle = run_source_cycle(DATA, SOURCES_CONFIG, load_categories(CATEGORIES_CONFIG), run_id)
        for rule in cycle["rules"]:
            telemetry.emit(run_id, "source_access", "ok" if rule["status"] == "ready" else "error", source_id=rule["source_id"], source=rule["name"], http_status=rule["http_status"], parser=rule["parser"], message=rule["reason"])
        if not cycle["ok"]:
            with run_lock:
                run_state["log"].append(cycle["reason"])
                run_state.update(status="failed", finished_at=datetime.now().isoformat(timespec="seconds"), exit_code=2)
            telemetry.emit(run_id, "source_replacement", "error", message=cycle["reason"])
            return
        telemetry.emit(run_id, "source_replacement", "ok", ready_sources=cycle["ready"], message="Active source set replaced with this run's approved feeds.")
        process = subprocess.Popen(command, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        with run_lock:
            run_state["process"] = process
        assert process.stdout is not None
        for line in process.stdout:
            with run_lock:
                run_state["log"].append(line.rstrip())
            telemetry.emit(run_id, "pipeline", "event", message=line.rstrip())
        exit_code = process.wait()
        with run_lock:
            run_state.update(status="succeeded" if exit_code == 0 else "failed", finished_at=datetime.now().isoformat(timespec="seconds"), exit_code=exit_code, process=None)
        telemetry.emit(run_id, "run_completion", "ok" if exit_code == 0 else "error", exit_code=exit_code)
        if exit_code == 0:
            copied = archive_outputs(DATA, run_id)
            telemetry.emit(run_id, "archive", "ok", artifacts=copied, message="Run outputs archived with the source rules.")

    @app.get("/")
    def index():
        if (FRONTEND_DIST / "index.html").exists():
            return send_from_directory(FRONTEND_DIST, "index.html")
        return jsonify({"error": "Frontend build is missing. Run npm.cmd run build in frontend."}), 503

    @app.get("/api/state")
    def state():
        view = snapshot()
        with run_lock:
            current_run = {key: value for key, value in run_state.items() if key != "process"}
            current_run["log"] = list(run_state["log"])
        return jsonify({"stats": view["stats"], "config": view["config"], "sources": view["sources"], "run": current_run})

    @app.get("/api/dashboard")
    def dashboard():
        view = snapshot()
        events = telemetry.read(400)
        status_counts = Counter(event.get("status", "unknown") for event in events)
        return jsonify({
            "stats": {**view["stats"], "telemetry_events": len(events), "failures": status_counts.get("error", 0)},
            "run": {key: value for key, value in run_state.items() if key not in ("process", "log")},
            "events": events[-80:], "telemetry": telemetry.summary(),
            "categories": load_categories(CATEGORIES_CONFIG), "credential_status": credential_status(),
            "credential_statuses": credential_statuses(),
        })

    @app.get("/api/categories")
    def categories_list():
        return jsonify({"categories": load_categories(CATEGORIES_CONFIG)})

    @app.put("/api/categories")
    def categories_update():
        categories = (request.get_json(silent=True) or {}).get("categories", [])
        if not isinstance(categories, list) or not categories:
            return jsonify({"ok": False, "error": "At least one category is required"}), 400
        ids = [str(item.get("id", "")).strip() for item in categories]
        if any(not item for item in ids) or len(ids) != len(set(ids)):
            return jsonify({"ok": False, "error": "Category identifiers must be unique and non-empty"}), 400
        save_categories(CATEGORIES_CONFIG, categories)
        return jsonify({"ok": True, "categories": categories})

    @app.get("/api/results")
    def results_list():
        articles = _read_jsonl(DATA / "processed" / "processed_articles.jsonl")
        selected = select_session_items(articles, _profile_from_config(_load_config()))
        return jsonify({"results": selected["selected"], "available": len(articles)})

    @app.get("/api/portfolio")
    def portfolio_list():
        return jsonify({"weights": {"business": 25, "reuse": 20, "technical": 20, "proof": 20, "relevance": 15}, "ratings": _portfolio_scores(_read_jsonl(DATA / "processed" / "processed_articles.jsonl"))})

    @app.get("/api/audit")
    def audit_list():
        return jsonify({"entries": _read_audit()[-500:]})

    @app.get("/api/runs")
    def archived_runs():
        return jsonify({"runs": list_runs(DATA)})

    @app.post("/api/source-cycle")
    def source_cycle_start():
        run_id = f"source-cycle-{uuid.uuid4().hex[:12]}"
        cycle = run_source_cycle(DATA, SOURCES_CONFIG, load_categories(CATEGORIES_CONFIG), run_id)
        for rule in cycle["rules"]:
            telemetry.emit(run_id, "source_access", "ok" if rule["status"] == "ready" else "error", source_id=rule["source_id"], source=rule["name"], message=rule["reason"])
        return jsonify(cycle), 200 if cycle["ok"] else 409

    @app.get("/api/source-lanes")
    def source_lanes_list():
        return jsonify({"lanes": source_lane_catalog()})

    @app.get("/api/content-intelligence")
    def content_intelligence_list():
        articles = _read_jsonl(DATA / "processed" / "processed_articles.jsonl")
        research_signals = _read_jsonl(RESEARCH_SIGNALS)
        strategy = load_strategy(CONTENT_STRATEGY)
        queue = build_idea_queue(articles + research_signals, strategy)
        return jsonify({
            "ideas": queue[:250],
            "counts": {"articles": len(articles), "research_signals": len(research_signals), "ideas": len(queue)},
            "audiences": list(AUDIENCE_TAXONOMY),
            "pillars": list(CONTENT_PILLARS),
            "collectors": list(COLLECTOR_CATALOG),
            "scoring_notice": "Evidence score only; it does not predict virality, revenue, or YouTube monetization approval.",
            "publishing": strategy.get("publishing", {"automatic_upload": False, "automatic_publish": False, "human_approval_required": True}),
        })

    @app.post("/api/research/collect")
    def research_collect():
        result = collect_research_signals(CONTENT_STRATEGY, RESEARCH_SIGNALS, DATA / "research" / "imports")
        records = _read_jsonl(DATA / "processed" / "processed_articles.jsonl") + _read_jsonl(RESEARCH_SIGNALS)
        exports = write_idea_exports(build_idea_queue(records, load_strategy(CONTENT_STRATEGY)), DATA / "exports")
        result["exports"] = {name: str(path.relative_to(BASE)) for name, path in exports.items()}
        telemetry.emit("research-collection", "research_collection", "ok" if result["ok"] else "error", collected=result["collected"], added=result["added"], message="Official API and approved-import research pass completed.")
        return jsonify(result), 200 if result["ok"] else 409

    @app.get("/api/source-registry")
    def source_registry_get():
        return jsonify(source_registry_payload(SOURCE_REGISTRY))

    @app.post("/api/source-registry/discover")
    def source_registry_discover():
        try:
            result = discover_source_candidates(CONTENT_STRATEGY, SOURCE_REGISTRY)
            telemetry.emit("source-discovery", "source_discovery", "ok", added=result["added"], discovered=result["discovered"], message="Novel domains were staged for trust and access review; none were activated.")
            return jsonify(result)
        except httpx.HTTPError as exc:
            telemetry.emit("source-discovery", "source_discovery", "error", message=str(exc)[:240])
            return jsonify({"ok": False, "error": str(exc)}), 502

    @app.get("/api/workspace")
    def workspace_get():
        return jsonify(_load_workspace())

    @app.post("/api/workspace/journal")
    def workspace_journal_add():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text", "")).strip()
        stage = str(payload.get("stage", "observe")).strip().lower()
        if not text or len(text) > 1000:
            return jsonify({"ok": False, "error": "Journal text must be between 1 and 1000 characters"}), 400
        if stage not in {"discover", "select", "template", "render", "approve", "publish", "observe"}:
            return jsonify({"ok": False, "error": "Unknown workflow stage"}), 400
        workspace = _load_workspace()
        entry = {"id": str(uuid.uuid4()), "text": text, "stage": stage, "created_at": datetime.now().isoformat(timespec="seconds"), "automation_candidate": bool(payload.get("automation_candidate", False))}
        workspace["journal"].insert(0, entry)
        _save_workspace(workspace)
        return jsonify({"ok": True, "entry": entry, "workspace": workspace}), 201

    @app.post("/api/workspace/templates")
    def workspace_template_add():
        payload = request.get_json(silent=True) or {}
        title = str(payload.get("title", "")).strip()
        source_title = str(payload.get("source_title", "")).strip()
        if not title or not source_title:
            return jsonify({"ok": False, "error": "Template title and source title are required"}), 400
        template = {
            "id": str(uuid.uuid4()),
            "title": title[:120],
            "source_title": source_title[:300],
            "source_url": str(payload.get("source_url", ""))[:1000],
            "hook": str(payload.get("hook", ""))[:500],
            "proof": str(payload.get("proof", ""))[:1000],
            "cta": str(payload.get("cta", ""))[:500],
            "format": str(payload.get("format", "signal-brief"))[:80],
            "status": "draft",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        workspace = _load_workspace()
        workspace["templates"].insert(0, template)
        _save_workspace(workspace)
        return jsonify({"ok": True, "template": template, "workspace": workspace}), 201

    @app.get("/api/events")
    def events_list():
        return jsonify({"events": telemetry.read(min(int(request.args.get("limit", 500)), 2000))})

    @app.get("/api/observability")
    def observability():
        """Return the complete persisted trace plus the active process buffer."""
        view = snapshot()
        events = telemetry.read(2000)
        with run_lock:
            run = {key: value for key, value in run_state.items() if key != "process"}
            run["log"] = list(run_state["log"])
        errors = [
            event for event in events
            if event.get("status") == "error"
            or any(token in str(event.get("message", "")).lower() for token in ("error", "failed", "blocked", "unavailable", "skipped"))
        ]
        return jsonify({
            "run": run,
            "config": view["config"],
            "sources": view["sources"],
            "events": events,
            "errors": errors[-200:],
            "stats": view["stats"],
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        })

    @app.get("/api/sources/preview")
    def source_preview():
        """Fetch a small, readable source preview; opening the original remains available."""
        url = str(request.args.get("url", "")).strip()
        if not url.startswith(("http://", "https://")):
            return jsonify({"ok": False, "error": "A valid http(s) source URL is required"}), 400
        started = time.perf_counter()
        try:
            response = httpx.get(
                url,
                timeout=20,
                follow_redirects=True,
                headers={"User-Agent": "ai-free-update-scrape/1.0 (+local source inspector)"},
            )
            content_type = response.headers.get("content-type", "")
            text = response.text if "html" in content_type or "text" in content_type else ""
            text = sub(r"(?is)<(script|style|noscript).*?>.*?</\\1>", " ", text)
            text = sub(r"(?s)<[^>]+>", " ", text)
            text = sub(r"\\s+", " ", unescape(text)).strip()
            return jsonify({
                "ok": response.is_success,
                "url": str(response.url),
                "status": response.status_code,
                "content_type": content_type,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "preview": text[:16000],
                "error": "" if response.is_success else f"Source returned HTTP {response.status_code}",
            })
        except httpx.HTTPError as exc:
            return jsonify({"ok": False, "url": url, "preview": "", "error": str(exc), "latency_ms": round((time.perf_counter() - started) * 1000)}), 400

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ready", "credential_status": credential_status(), "credential_statuses": credential_statuses()})

    @app.get("/api/yt-auto")
    def yt_auto_overview():
        return jsonify({"status": yt_auto_status(), "tools": [tool.as_mcp() for tool in YT_AUTO_TOOLS.values()]})

    @app.post("/api/yt-auto/tools/<tool_name>")
    def yt_auto_tool_call(tool_name: str):
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify({"ok": False, "error": "YT Auto tools are localhost-only"}), 403
        try:
            result = call_yt_auto_tool(tool_name, request.get_json(silent=True) or {})
            return jsonify(result), 200 if result.get("ok", True) else 400
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except (ValueError, subprocess.TimeoutExpired) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/mcp")
    def mcp_endpoint():
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify({"error": "MCP endpoint is localhost-only"}), 403
        response, status_code = handle_yt_auto_jsonrpc(request.get_json(silent=True) or {})
        return jsonify(response), status_code

    @app.get("/api/credentials/status")
    def credentials_status():
        return jsonify({"providers": credential_statuses()})

    @app.post("/api/credentials")
    def credentials_save():
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify({"ok": False, "error": "Credential updates are localhost-only"}), 403
        payload = request.get_json(silent=True) or {}
        provider = str(payload.get("provider", "")).strip()
        value = str(payload.get("api_key", ""))
        try:
            env_name = save_user_credential(provider, value)
            return jsonify({"ok": True, "provider": provider, "env_name": env_name, "status": "configured"})
        except (ValueError, RuntimeError, OSError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/models")
    def models_list():
        provider = request.args.get("provider", "all")
        models = []
        errors = {}
        targets = list(PROVIDERS) if provider == "all" else [provider]
        with ThreadPoolExecutor(max_workers=len(targets) or 1) as executor:
            futures = {executor.submit(discover_models, target): target for target in targets}
            for future in as_completed(futures):
                target = futures[future]
                try:
                    models.extend(future.result())
                except Exception as exc:
                    errors[target] = str(exc)
        if provider in ("all", "local"):
            models.extend(discover_local_models())
        return jsonify({"models": models, "errors": errors, "credential_statuses": credential_statuses()})

    @app.post("/api/models/test")
    def model_test():
        payload = request.get_json(silent=True) or {}
        model = str(payload.get("model", "")).strip()
        provider = str(payload.get("provider", "nvidia")).strip()
        if not model:
            return jsonify({"ok": False, "error": "Select a model first"}), 400
        try:
            return jsonify({"ok": True, "result": test_model(model, provider)})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/sources/test")
    def source_test():
        source = request.get_json(silent=True) or {}
        url = str(source.get("url", ""))
        if not url.startswith(("http://", "https://")):
            return jsonify({"ok": False, "error": "A valid http(s) URL is required"}), 400
        started = time.perf_counter()
        try:
            response = httpx.get(url, timeout=min(int(source.get("timeout", 20)), 60), follow_redirects=True, headers={"User-Agent": "ai-free-update-scrape/1.0"})
            return jsonify({"ok": response.is_success, "status": response.status_code, "content_type": response.headers.get("content-type", ""), "bytes": len(response.content), "latency_ms": round((time.perf_counter() - started) * 1000)})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc), "latency_ms": round((time.perf_counter() - started) * 1000)}), 400

    @app.post("/api/run/cancel")
    def cancel_run():
        with run_lock:
            process = run_state.get("process")
            if not process or process.poll() is not None:
                return jsonify({"ok": False, "error": "No active run"}), 409
            process.terminate()
        return jsonify({"ok": True, "status": "cancelling"})

    @app.put("/api/config")
    def save_config():
        clean, errors = _validate_config(request.get_json(silent=True) or {})
        if errors:
            return jsonify({"ok": False, "errors": errors}), 400
        DASHBOARD_CONFIG.write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")
        return jsonify({"ok": True, "config": clean})

    @app.put("/api/sources")
    def save_sources():
        payload = request.get_json(silent=True) or {}
        clean = {"rss": [], "scrape": []}
        for group in clean:
            for source in payload.get(group, []):
                name = str(source.get("name", "")).strip()
                url = str(source.get("url", "")).strip()
                if not name or not url.startswith(("http://", "https://")):
                    return jsonify({"ok": False, "error": "Every source needs a name and an http(s) URL"}), 400
                item = {"name": name, "url": url, "enabled": bool(source.get("enabled", True))}
                if group == "scrape":
                    item["type"] = str(source.get("type", "web")).strip() or "web"
                    if source.get("limit") not in (None, ""):
                        item["limit"] = int(source["limit"])
                clean[group].append(item)
        SOURCES_CONFIG.write_text(yaml.safe_dump(clean, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return jsonify({"ok": True, "sources": clean})

    @app.post("/api/run")
    def start_run():
        with run_lock:
            if run_state["status"] == "running":
                return jsonify({"ok": False, "error": "A scrape is already running"}), 409
        config, errors = _validate_config(request.get_json(silent=True) or _load_config())
        if errors:
            return jsonify({"ok": False, "errors": errors}), 400
        DASHBOARD_CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        threading.Thread(target=execute_run, args=(config,), daemon=True).start()
        return jsonify({"ok": True, "status": "starting"}), 202

    @app.get("/<path:path>")
    def frontend_assets(path: str):
        if (FRONTEND_DIST / path).exists():
            return send_from_directory(FRONTEND_DIST, path)
        if (FRONTEND_DIST / "index.html").exists():
            return send_from_directory(FRONTEND_DIST, "index.html")
        return jsonify({"error": "Not found"}), 404

    return app


def run(host: str = "127.0.0.1", port: int = 5050, debug: bool = True) -> None:
    build_app().run(host=host, port=port, debug=debug, use_reloader=False)
