from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ai_free_update_scrape.content_intelligence import (
    AUDIENCE_TAXONOMY,
    CONTENT_PILLARS,
    build_idea_queue,
    classify_record,
    write_idea_exports,
)
from ai_free_update_scrape.research import COLLECTOR_CATALOG, discover_source_candidates
from ai_free_update_scrape.web.app import build_app


def test_taxonomies_cover_requested_audiences_pillars_and_both_formats():
    audience_ids = {item["id"] for item in AUDIENCE_TAXONOMY}
    pillar_ids = {item["id"] for item in CONTENT_PILLARS}
    assert {
        "solo_freelancers_operators", "vibe_coders", "developers", "small_businesses", "corporate_individuals"
    } <= audience_ids
    assert {
        "news_updates", "tips_tricks", "pain_point_solutions", "manual_task_automation", "concepts_education",
        "tool_instructions", "systems_mindset", "use_cases_portfolio", "promotions_offers", "comparisons_reviews",
    } <= pillar_ids
    result = classify_record({"title": "Docker dependency error", "summary": "Developers are stuck on a failed CI/CD pipeline."})
    assert result["audiences"][0]["id"] == "developers"
    assert result["pillars"][0]["id"] == "pain_point_solutions"
    assert set(result["format_options"]) == {"short", "long"}


def test_content_velocity_score_keeps_component_evidence_visible():
    now = datetime(2026, 7, 16, 12, tzinfo=timezone.utc)
    strategy = {
        "offers": [{"name": "Automation audit", "enabled": True, "keywords": ["automation"]}],
        "scoring": {"keyword_growth_velocity": 0.4, "source_engagement": 0.3, "monetization_intent": 0.3},
    }
    queue = build_idea_queue([{
        "title": "Automation workflow error", "summary": "A small business support bot is stuck.",
        "source": "Allowed API", "source_kind": "question", "url": "https://example.test/question/1",
        "published": now.isoformat(), "engagement_score": 80, "source_trust_score": 75,
    }], strategy, now=now)
    idea = queue[0]
    expected = round(
        idea["score_components"]["keyword_growth_velocity"] * .4
        + idea["score_components"]["source_engagement"] * .3
        + idea["score_components"]["monetization_intent"] * .3,
        2,
    )
    assert idea["content_velocity_score"] == expected
    assert idea["offer_matches"] == ["Automation audit"]
    assert idea["approval_required"] is True
    assert idea["review_status"] == "research_ready"


def test_missing_metrics_are_named_instead_of_invented():
    idea = build_idea_queue([{"title": "A useful AI update", "url": "https://example.test/update", "source": "Example"}])[0]
    assert idea["score_components"]["keyword_growth_velocity"] is None
    assert idea["score_components"]["source_engagement"] is None
    assert "timestamp or 72-hour history" in idea["data_gaps"]
    assert "source trust review" in idea["data_gaps"]
    assert idea["review_status"] == "needs_review"


def test_unmatched_public_question_defaults_to_pain_solution_not_news():
    result = classify_record({"title": "How can I update this source?", "source_kind": "stackexchange_question", "pain_signal": True})
    assert result["pillars"][0]["id"] == "pain_point_solutions"
    assert "source pain signal" in result["pillars"][0]["matched_keywords"]


def test_idea_exports_include_json_csv_and_reviewable_markdown(tmp_path: Path):
    queue = build_idea_queue([{"title": "Python automation tutorial", "summary": "How to use a repeatable workflow.", "url": "https://example.test/tutorial", "source": "Example"}])
    outputs = write_idea_exports(queue, tmp_path)
    assert set(outputs) == {"json", "csv", "markdown"}
    assert all(path.exists() for path in outputs.values())
    assert "human approval required" in outputs["markdown"].read_text(encoding="utf-8")


def test_collector_catalog_excludes_stealth_review_scraping():
    by_id = {item["id"]: item for item in COLLECTOR_CATALOG}
    assert by_id["reddit"]["access"] == "Reddit Data API"
    assert "direct page scraping is disabled" in by_id["reddit"]["restriction"]
    assert by_id["review_import"]["access"] == "local CSV or JSONL import"
    assert "No stealth browser" in by_id["review_import"]["restriction"]


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return self

    def json(self):
        return self.payload


class _FakeClient:
    def get(self, url, **_kwargs):
        if url.endswith("newstories.json"):
            return _FakeResponse([10, 11, 12, 13])
        story_id = int(url.rsplit("/", 1)[1].split(".", 1)[0])
        payloads = {
            10: {"title": "AI automation source", "url": "https://newsource.example/story"},
            11: {"title": "LLM duplicate", "url": "https://newsource.example/another"},
            12: {"title": "AI over insecure transport", "url": "http://ignored.example/story"},
            13: {"title": "Unrelated local event", "url": "https://unrelated.example/story"},
        }
        return _FakeResponse(payloads[story_id])


def test_source_discovery_persists_unique_review_candidates_without_activation(tmp_path: Path):
    config = tmp_path / "content_strategy.yaml"
    config.write_text("source_discovery:\n  enabled: true\n  hacker_news_story_limit: 25\n", encoding="utf-8")
    registry = tmp_path / "source_registry.json"
    first = discover_source_candidates(config, registry, client=_FakeClient())
    second = discover_source_candidates(config, registry, client=_FakeClient())
    stored = json.loads(registry.read_text(encoding="utf-8"))
    assert first["added"] == 1
    assert second["added"] == 0
    assert stored[0]["domain"] == "newsource.example"
    assert stored[0]["relevance_keywords"] == ["llm"]
    assert stored[0]["status"] == "review_required"
    assert stored[0]["activation_allowed"] is False


def test_content_intelligence_endpoint_exposes_queue_and_guardrails():
    response = build_app().test_client().get("/api/content-intelligence")
    assert response.status_code == 200
    assert len(response.json["audiences"]) >= 7
    assert len(response.json["pillars"]) >= 10
    assert response.json["publishing"]["automatic_publish"] is False
    assert "does not predict" in response.json["scoring_notice"]
