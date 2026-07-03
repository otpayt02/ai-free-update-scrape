"""Entry point for one scrape run with exports for digest, Sheets, and Shorts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml
from rich.console import Console

from .catalog import classify_topics, time_slot_for_now
from .categories import classify_article, load_categories
from .deliver.digest import write_digest
from .enrich.alternatives import find_alternatives
from .enrich.detector import detect_tool
from .export.sheet import write_articles_csv, write_dashboard_html
from .export.workbook import build_dashboard_workbook
from .ingest.hn import fetch_hn_top
from .ingest.rss import run_rss_ingest
from .ingest.web import fetch_source
from .plan.shorts import build_shorts_plan, write_shorts_csv, write_shorts_markdown
from .providers import credential_status, discover_local_models, discover_models
from .session import DEFAULT_SESSION, SessionProfile, select_session_items
from .rank.ranker import load_use_cases, rank_article

BASE = Path(__file__).parent.parent.parent
CONFIG = BASE / "config"
DATA = BASE / "data"
console = Console()

def provider_available(provider: str) -> bool:
    """Report provider readiness without exposing credentials."""
    if provider.endswith("local") or provider in ("lm-studio", "vllm", "llama-cpp"):
        return any(model["provider"] == provider for model in discover_local_models())
    return credential_status(provider) == "configured"


def enrich_with_provider(articles: list[dict], model: str, provider: str) -> list[dict]:
    """LLM-assisted enrichment with detection, alternatives, and ranking."""

    use_cases = load_use_cases(CONFIG / "personal_use_cases.yaml")
    enriched = []
    for index, article in enumerate(articles[:50]):
        article["topics"] = article.get("topics") or classify_topics(" ".join([
            article.get("title", ""),
            article.get("summary", ""),
            article.get("source", ""),
        ]))
        detected = detect_tool(article, model, provider)
        with_alts = find_alternatives(detected, model, provider) if detected.get("detection", {}).get("new_tool") else {**detected, "alternatives": []}
        ranked = rank_article(with_alts, use_cases, model, provider)
        enriched.append(ranked)
        if (index + 1) % 10 == 0:
            console.print(f"  Enriched {index + 1}/{min(50, len(articles))}...")
    return enriched


def enrich_without_model(articles: list[dict]) -> list[dict]:
    """Free fallback that uses source priority and topic heuristics only."""

    source_priority = {
        "HuggingFace Blog": 10,
        "OpenAI Blog": 10,
        "DeepMind Blog": 9,
        "Papers With Code": 9,
        "Hacker News": 8,
        "Simon Willison": 8,
        "TechCrunch AI": 7,
        "The Verge AI": 7,
        "Ars Technica AI": 6,
        "Product Hunt": 6,
        "Sebastian Raschka": 8,
    }
    enriched = []
    for article in articles:
        topics = article.get("topics") or classify_topics(" ".join([
            article.get("title", ""),
            article.get("summary", ""),
            article.get("source", ""),
        ]))
        score = source_priority.get(article.get("source", ""), 5)
        if "free" in topics:
            score += 1
        enriched.append({
            **article,
            "topics": topics,
            "detection": {"new_tool": True, "type": "unclear", "tool_name": article.get("title", "")},
            "alternatives": [],
            "ranking": {
                "top_score": score,
                "reason": f"Source: {article.get('source', 'unknown')} and topics: {', '.join(topics)}.",
            },
        })
    return enriched


def _load_sources() -> list[dict]:
    with open(CONFIG / "sources.yaml", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return payload.get("rss", []) + payload.get("scrape", [])


def _append_articles(path: Path, articles: list[dict]) -> int:
    existing_urls: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                existing_urls.add(json.loads(line)["url"])
            except Exception:
                pass

    new_count = 0
    with path.open("a", encoding="utf-8") as handle:
        for article in articles:
            if article["url"] in existing_urls:
                continue
            handle.write(json.dumps(article) + "\n")
            existing_urls.add(article["url"])
            new_count += 1
    return new_count


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AI update scrape and Shorts planning pipeline.")
    parser.add_argument("--plan-days", type=int, default=DEFAULT_SESSION.plan_days)
    parser.add_argument("--plan-per-day", type=int, default=DEFAULT_SESSION.plan_per_day)
    parser.add_argument("--rss-limit", type=int, default=DEFAULT_SESSION.rss_limit)
    parser.add_argument("--hn-limit", type=int, default=DEFAULT_SESSION.hn_limit)
    parser.add_argument("--web-limit", type=int, default=DEFAULT_SESSION.web_limit)
    parser.add_argument("--industry-target", type=int, default=DEFAULT_SESSION.ai_industry_items)
    parser.add_argument("--free-target", type=int, default=DEFAULT_SESSION.free_items)
    parser.add_argument("--max-items", type=int, default=DEFAULT_SESSION.max_items_per_run)
    parser.add_argument("--llm-model", default=DEFAULT_SESSION.llm_model)
    parser.add_argument("--provider", default="nvidia")
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args(argv)

    console.print("[bold green]ai-free-update-scrape[/bold green] starting...")
    console.print(f"  Scrape window: {time_slot_for_now(datetime.now())}")
    console.print(f"  Session target: {args.industry_target} industry + {args.free_target} free = at least {args.industry_target + args.free_target} items")

    sources = [source for source in _load_sources() if source.get("enabled", True)]

    raw_path = DATA / "raw" / "raw_articles.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    rss_sources = [source for source in sources if source.get("type", "rss") in ("rss", "", None)]
    rss_sources = rss_sources[: max(1, args.rss_limit)]
    rss_count = run_rss_ingest(rss_sources, raw_path)
    console.print(f"  RSS: {rss_count} new articles")

    scraped_sources = [source for source in sources if source.get("type") not in ("rss", "", None)]
    scraped_count = 0
    if scraped_sources:
        scraped_articles: list[dict] = []
        for source in scraped_sources[: max(1, args.web_limit)]:
            try:
                scraped_articles.extend(fetch_source(source))
            except Exception as exc:
                console.print(f"  [yellow]Scrape skipped[/yellow] {source.get('name', source.get('url', 'unknown'))}: {exc}")
        scraped_count = _append_articles(raw_path, scraped_articles)
    console.print(f"  Web scrape: {scraped_count} new articles")

    hn_articles = fetch_hn_top(limit=args.hn_limit)
    hn_new = _append_articles(raw_path, hn_articles)
    console.print(f"  HN: {hn_new} new articles")

    articles = []
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        try:
            articles.append(json.loads(line))
        except Exception:
            pass
    console.print(f"  Total articles loaded: {len(articles)}")
    categories = load_categories(CONFIG / "categories.json")
    for article in articles:
        article["categories"] = classify_article(article, categories)

    use_llm = provider_available(args.provider) and not args.skip_llm
    if use_llm:
        model = args.llm_model
        if not model:
            available = discover_models(args.provider) if not args.provider.endswith("local") else discover_local_models()
            matching = [item["id"] for item in available if item.get("provider") == args.provider]
            if not matching:
                raise RuntimeError(f"No models were returned for {args.provider}")
            model = sorted(matching)[-1]
        console.print(f"  [bold cyan]{args.provider} configured[/bold cyan] - running enrichment ({model})")
        enriched = enrich_with_provider(articles, model, args.provider)
    else:
        console.print("  [yellow]NVIDIA enrichment unavailable or skipped[/yellow] - using deterministic fallback scoring")
        enriched = enrich_without_model(articles)

    profile = SessionProfile(
        min_items=args.industry_target + args.free_target,
        ai_industry_items=args.industry_target,
        free_items=args.free_target,
        max_items_per_run=args.max_items,
        rss_limit=args.rss_limit,
        hn_limit=args.hn_limit,
        web_limit=args.web_limit,
        plan_days=args.plan_days,
        plan_per_day=args.plan_per_day,
        llm_model=args.llm_model,
    )
    selected = select_session_items(enriched[: args.max_items], profile)
    session_items = selected["selected"]
    console.print(f"  Selected for session view: {len(session_items)} items")

    processed_path = DATA / "processed" / "processed_articles.jsonl"
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    with processed_path.open("w", encoding="utf-8") as handle:
        for article in enriched:
            handle.write(json.dumps(article) + "\n")

    digest_path = write_digest(
        session_items,
        digests_dir=DATA / "digests",
        ledger_path=DATA / "ledger.jsonl",
        llm_mode=use_llm,
    )

    articles_csv = write_articles_csv(session_items, DATA / "exports" / "articles_sheet.csv")
    shorts_plan = build_shorts_plan(session_items, days=args.plan_days, per_day=args.plan_per_day)
    shorts_csv = write_shorts_csv(shorts_plan, DATA / "exports" / "shorts_plan.csv")
    write_shorts_markdown(shorts_plan, DATA / "exports" / "shorts_plan.md")
    workbook_path = build_dashboard_workbook(
        articles=enriched,
        shorts_plan=[row.__dict__ for row in shorts_plan],
        digest_path=digest_path,
        output_path=DATA / "exports" / "dashboard.xlsx",
    )
    dashboard_path = write_dashboard_html(
        digest_path=digest_path,
        shorts_csv=shorts_csv,
        articles_csv=articles_csv,
        output_path=DATA / "exports" / "dashboard.html",
    )

    console.print(f"[bold]Digest written:[/bold] {digest_path}")
    console.print(f"[bold]Articles CSV written:[/bold] {articles_csv}")
    console.print(f"[bold]Shorts CSV written:[/bold] {shorts_csv}")
    console.print(f"[bold]Workbook written:[/bold] {workbook_path}")
    console.print(f"[bold]Dashboard written:[/bold] {dashboard_path}")
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    run()
