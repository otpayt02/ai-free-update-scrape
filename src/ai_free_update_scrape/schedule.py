"""Entry point: run the full pipeline once. Schedule via Windows Task Scheduler."""
import yaml
import json
import sys
from pathlib import Path
from rich.console import Console

from .ingest.rss import run_rss_ingest
from .ingest.hn import fetch_hn_top
from .deliver.digest import write_digest

BASE = Path(__file__).parent.parent.parent
CONFIG = BASE / "config"
DATA = BASE / "data"
console = Console()

OLLAMA_MODEL = "phi4-reasoning:14b"  # swap to qwen2.5-coder:32b when ready


def ollama_available() -> bool:
    try:
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


def enrich_with_ollama(articles: list[dict]) -> list[dict]:
    from .enrich.detector import detect_tool
    from .enrich.alternatives import find_alternatives
    from .rank.ranker import rank_article, load_use_cases
    use_cases = load_use_cases(CONFIG / "personal_use_cases.yaml")
    enriched = []
    for i, article in enumerate(articles[:50]):
        detected = detect_tool(article, OLLAMA_MODEL)
        if detected.get("detection", {}).get("new_tool"):
            with_alts = find_alternatives(detected, OLLAMA_MODEL)
        else:
            with_alts = {**detected, "alternatives": []}
        ranked = rank_article(with_alts, use_cases, OLLAMA_MODEL)
        enriched.append(ranked)
        if (i + 1) % 10 == 0:
            console.print(f"  Enriched {i+1}/{min(50, len(articles))}...")
    return enriched


def enrich_without_ollama(articles: list[dict]) -> list[dict]:
    """No-LLM fallback: mark every article visible, score by source priority."""
    SOURCE_PRIORITY = {
        "HuggingFace Blog": 10, "OpenAI Blog": 10, "DeepMind Blog": 9,
        "Papers With Code": 9, "Hacker News": 8, "Simon Willison": 8,
        "TechCrunch AI": 7, "The Verge AI": 7, "Ars Technica AI": 6,
        "Product Hunt": 6, "Sebastian Raschka": 8,
    }
    enriched = []
    for article in articles:
        score = SOURCE_PRIORITY.get(article.get("source", ""), 5)
        enriched.append({
            **article,
            "detection": {"new_tool": True, "type": "unclear", "tool_name": article.get("title", "")},
            "alternatives": [],
            "ranking": {
                "top_score": score,
                "reason": f"Source: {article.get('source', 'unknown')} — enable Ollama for AI-powered ranking."
            },
        })
    return enriched


def run():
    console.print("[bold green]ai-free-update-scrape[/bold green] starting...")

    with open(CONFIG / "sources.yaml") as f:
        sources = yaml.safe_load(f)

    raw_path = DATA / "raw" / "raw_articles.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # Ingest RSS
    rss_count = run_rss_ingest(sources.get("rss", []), raw_path)
    console.print(f"  RSS: {rss_count} new articles")

    # Ingest HN
    hn_articles = fetch_hn_top(limit=30)
    seen_urls: set[str] = set()
    if raw_path.exists():
        for line in raw_path.read_text().splitlines():
            try:
                seen_urls.add(json.loads(line)["url"])
            except Exception:
                pass
    hn_new = 0
    with raw_path.open("a") as f:
        for a in hn_articles:
            if a["url"] not in seen_urls:
                f.write(json.dumps(a) + "\n")
                hn_new += 1
    console.print(f"  HN: {hn_new} new articles")

    # Load raw articles
    articles = []
    for line in raw_path.read_text().splitlines():
        try:
            articles.append(json.loads(line))
        except Exception:
            pass
    console.print(f"  Total articles loaded: {len(articles)}")

    # Enrich
    use_llm = ollama_available()
    if use_llm:
        console.print(f"  [bold cyan]Ollama detected[/bold cyan] — running LLM enrichment ({OLLAMA_MODEL})")
        enriched = enrich_with_ollama(articles)
    else:
        console.print("  [yellow]Ollama not running[/yellow] — using fast no-LLM mode (all articles shown, ranked by source)")
        enriched = enrich_without_ollama(articles)

    # Save processed
    processed_path = DATA / "processed" / "processed_articles.jsonl"
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    with processed_path.open("w") as f:
        for a in enriched:
            f.write(json.dumps(a) + "\n")

    # Deliver
    digest_path = write_digest(
        enriched,
        digests_dir=DATA / "digests",
        ledger_path=DATA / "ledger.jsonl",
        llm_mode=use_llm,
    )
    console.print(f"[bold]Digest written:[/bold] {digest_path}")
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    run()
