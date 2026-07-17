from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ai_free_update_scrape.categories import classify_article, default_categories
from ai_free_update_scrape.providers import credential_status
from ai_free_update_scrape.source_cycle import discover_candidates, run_source_cycle, source_lane_catalog
from ai_free_update_scrape.web.app import build_app


def test_taxonomy_has_thirty_unique_categories():
    categories = default_categories()
    assert len(categories) == 30
    assert len({category["id"] for category in categories}) == 30


def test_category_classification_uses_configured_keywords():
    matches = classify_article({"title": "New MCP server released", "summary": "open source"}, default_categories())
    assert "mcp-servers-and-integrations" in matches
    assert "open-source-repositories" in matches


def test_missing_credential_exposes_presence_only(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    assert credential_status() == "missing"


def test_control_center_endpoints(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr("ai_free_update_scrape.web.app.discover_models", lambda provider: [])
    monkeypatch.setattr("ai_free_update_scrape.web.app.discover_local_models", lambda: [])
    client = build_app().test_client()
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/dashboard").status_code == 200
    assert client.get("/api/categories").status_code == 200
    assert client.get("/api/results").status_code == 200
    response = client.get("/api/models")
    assert response.status_code == 200
    assert "models" in response.json
    assert response.json["credential_statuses"]["nvidia"] == "missing"


def test_credential_write_returns_presence_only(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("ai_free_update_scrape.web.app.save_user_credential", lambda provider, value: "OPENAI_API_KEY")
    response = build_app().test_client().post(
        "/api/credentials", json={"provider": "openai", "api_key": "secret-value-not-returned"}
    )
    assert response.status_code == 200
    assert "api_key" not in response.json
    assert response.json["env_name"] == "OPENAI_API_KEY"


def test_source_probe_rejects_non_http_url():
    response = build_app().test_client().post("/api/sources/test", json={"url": "file:///secret"})
    assert response.status_code == 400


def test_observability_exposes_persisted_trace_and_live_state():
    response = build_app().test_client().get("/api/observability")
    assert response.status_code == 200
    assert {"config", "sources", "events", "errors", "run", "updated_at"} <= set(response.json)


def test_source_preview_rejects_non_http_url():
    response = build_app().test_client().get("/api/sources/preview?url=file:///secret")
    assert response.status_code == 400


def test_source_cycle_replaces_active_sources_and_archives_rules(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def planned(candidate: dict) -> dict:
        return {**candidate, "status": "ready" if candidate["name"] == "Hugging Face Blog" else "rejected", "reason": "test rule", "http_status": 200, "robots": "reviewed", "parser": "feedparser", "instruction": "test", "selector_notes": "test"}
    monkeypatch.setattr("ai_free_update_scrape.source_cycle.plan_candidate", planned)
    source_path = tmp_path / "sources.yaml"
    source_path.write_text("rss:\n  - name: old\n    url: https://old.example/rss\nscrape: []\n", encoding="utf-8")
    result = run_source_cycle(tmp_path, source_path, [{"name": "Models", "enabled": True}, {"name": "Blocked", "enabled": True}], "run-test")
    assert result["ok"] is True
    assert result["ready"] == 1
    assert "Hugging Face Blog" in source_path.read_text(encoding="utf-8")
    assert (tmp_path / "runs" / "run-test" / "source_rules.json").exists()
    assert len(__import__("json").loads((tmp_path / "audit_queue.json").read_text(encoding="utf-8"))) == len(result["rules"])


def test_discovery_uses_diverse_source_specific_feeds():
    candidates = discover_candidates(
        [{"name": "Foundation model releases", "enabled": True}, {"name": "Coding assistants", "enabled": True}],
        "run-diverse",
    )
    assert len(candidates) >= 3
    assert len({candidate["url"] for candidate in candidates}) == len(candidates)
    assert all("news.google.com" not in candidate["url"] for candidate in candidates)
    assert all(candidate["origin"] == "curated source-specific RSS discovery" for candidate in candidates)


def test_video_source_lanes_expose_only_safe_collection_options():
    lanes = source_lane_catalog()
    assert [lane["id"] for lane in lanes] == ["news_updates", "development_workflows", "tutorials", "pain_points", "website_design_problems"]
    pain_points = next(lane for lane in lanes if lane["id"] == "pain_points")
    reddit = next(source for source in pain_points["candidates"] if source["name"] == "Reddit Data API")
    assert reddit["kind"] == "official API"
    assert "direct scraping is disabled" in reddit["setup"]


def test_source_lane_endpoint_returns_catalog():
    response = build_app().test_client().get("/api/source-lanes")
    assert response.status_code == 200
    assert len(response.json["lanes"]) == 5


def test_source_cycle_does_not_replace_sources_when_none_are_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr("ai_free_update_scrape.source_cycle.plan_candidate", lambda candidate: {**candidate, "status": "rejected", "reason": "blocked", "http_status": 403, "robots": "reviewed", "parser": "feedparser", "instruction": "", "selector_notes": ""})
    source_path = tmp_path / "sources.yaml"
    original = "rss:\n  - name: old\n    url: https://old.example/rss\nscrape: []\n"
    source_path.write_text(original, encoding="utf-8")
    result = run_source_cycle(tmp_path, source_path, [{"name": "Models", "enabled": True}], "run-blocked")
    assert result["ok"] is False
    assert source_path.read_text(encoding="utf-8") == original


def test_restored_operational_read_endpoints():
    client = build_app().test_client()
    assert client.get("/api/portfolio").status_code == 200
    assert client.get("/api/audit").status_code == 200
    assert client.get("/api/runs").status_code == 200


def test_yt_auto_mcp_lists_guarded_tools(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("ai_free_update_scrape.web.app.yt_auto_status", lambda: {"connected": True, "batches": []})
    client = build_app().test_client()
    response = client.get("/api/yt-auto")
    assert response.status_code == 200
    tools = {tool["name"]: tool for tool in response.json["tools"]}
    assert tools["yt_auto_qa_batch"]["annotations"]["enabled"] is True
    assert tools["yt_auto_publish_batch"]["annotations"]["enabled"] is False


def test_mcp_initialize_and_tool_list():
    client = build_app().test_client()
    initialized = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    listed = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert initialized.status_code == 200
    assert initialized.json["result"]["serverInfo"]["name"] == "yt-auto-control-center"
    assert listed.status_code == 200
    assert len(listed.json["result"]["tools"]) >= 5


def test_mcp_rejects_unsafe_batch_identifier():
    response = build_app().test_client().post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "yt_auto_qa_batch", "arguments": {"batch_id": "../secret"}}},
    )
    assert response.status_code == 400
    assert response.json["error"]["code"] == -32602


def test_workspace_journal_and_template_routes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr("ai_free_update_scrape.web.app.WORKSPACE_PATH", tmp_path / "workspace.json")
    client = build_app().test_client()
    journal = client.post("/api/workspace/journal", json={"text": "Reviewed the selected signal", "stage": "select", "automation_candidate": True})
    template = client.post("/api/workspace/templates", json={"title": "Signal Brief", "source_title": "A real source", "hook": "Why this matters"})
    saved = client.get("/api/workspace")
    assert journal.status_code == 201
    assert template.status_code == 201
    assert saved.json["journal"][0]["automation_candidate"] is True
    assert saved.json["templates"][0]["status"] == "draft"
