from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ai_free_update_scrape.categories import classify_article, default_categories
from ai_free_update_scrape.providers import credential_status
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
