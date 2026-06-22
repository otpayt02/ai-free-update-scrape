"""Entry point: run the full pipeline once. Schedule via Windows Task Scheduler."""
import yaml
import json
from pathlib import Path
from rich.console import Console

from .ingest.rss import run_rss_ingest
from .ingest.hn import fetch_hn_top
from .enrich.detector import detect_tool
from .enrich.alternatives import find_alternatives
from .rank.ranker import rank_article, load_use_cases
from .deliver.digest import write_digest

BASE = Path(__file__).parent.parent.parent
CONFIG = BASE / "config"
DATA = BASE / "data"
console = Console()

OLLAMA_MODEL = "qwen2.5-coder:32b"  # swap to deepseek-r1:32b for reasoning


def run():
    console.print("[bold green]ai-free-update-scrape[/bold green] starting...")

    # Load config
    with open(CONFIG / "sources.yaml") as f:
        sources = yaml.safe_load(f)
    use_cases = load_use_cases(CONFIG / "personal_use_cases.yaml")

    raw_path = DATA / "raw" / "raw_articles.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # Ingest RSS
    rss_count = run_rss_ingest(sources.get("rss", []), raw_path)
    console.print(f"  RSS: {rss_count} new articles")

    # Ingest HN
    hn_articles = fetch_hn_top(limit=30)
    seen_urls = set()
    if raw_path.exists():
        for line in raw_path.read_text().splitlines():
            try:
                seen_urls.add(json.loads(line)["url"])
            except Exception:
                pass
    with raw_path.open("a") as f:
        hn_new = 0
        for a in hn_articles:
            if a["url"] not in seen_urls:
                f.write(json.dumps(a) + "\n")
                hn_new += 1
    console.print(f"  HN: {hn_new} new articles")

    # Load all raw articles from today
    articles = []
    for line in raw_path.read_text().splitlines():
        try:
            articles.append(json.loads(line))
        except Exception:
            pass
    console.print(f"  Total articles to enrich: {len(articles)}")

    # Enrich
    enriched = []
    for i, article in enumerate(articles[:50]):  # cap at 50 per run to save LLM calls
        detected = detect_tool(article, OLLAMA_MODEL)
        if detected.get("detection", {}).get("new_tool"):
            with_alts = find_alternatives(detected, OLLAMA_MODEL)
        else:
            with_alts = {**detected, "alternatives": []}
        ranked = rank_article(with_alts, use_cases, OLLAMA_MODEL)
        enriched.append(ranked)
        if (i + 1) % 10 == 0:
            console.print(f"  Enriched {i+1}/{min(50, len(articles))}...")

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
    )
    console.print(f"[bold]Digest written:[/bold] {digest_path}")
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    run()
