"""Run the compliance-first research, source-discovery, and idea-export cycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "src"))

from ai_free_update_scrape.content_intelligence import build_idea_queue, load_strategy, write_idea_exports  # noqa: E402
from ai_free_update_scrape.research import collect_research_signals, discover_source_candidates  # noqa: E402


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect approved research signals, stage novel sources, and rebuild the video idea queue.")
    parser.add_argument("--collect", action="store_true", help="Run configured official-API and approved-import collectors.")
    parser.add_argument("--discover-sources", action="store_true", help="Stage novel HN-linked domains for human trust review.")
    parser.add_argument("--ideas-only", action="store_true", help="Skip network collection and rebuild ideas from stored evidence.")
    args = parser.parse_args(argv)
    run_all = not (args.collect or args.discover_sources or args.ideas_only)
    config = BASE / "config" / "content_strategy.yaml"
    summary: dict[str, object] = {}

    if run_all or args.collect:
        summary["research"] = collect_research_signals(
            config,
            BASE / "data" / "research" / "signals.jsonl",
            BASE / "data" / "research" / "imports",
        )
    if run_all or args.discover_sources:
        try:
            discovery = discover_source_candidates(config, BASE / "data" / "source_registry.json")
            summary["source_discovery"] = {
                "ok": discovery["ok"],
                "added": discovery["added"],
                "discovered": discovery["discovered"],
                "removed_out_of_scope": discovery["removed_out_of_scope"],
                "registry_size": len(discovery["registry"]),
                "activation_requires_human_review": discovery["activation_requires_human_review"],
            }
        except Exception as exc:  # keep stored-evidence exports available when a public API is unavailable
            summary["source_discovery"] = {"ok": False, "error": str(exc)[:240]}

    records = _read_jsonl(BASE / "data" / "processed" / "processed_articles.jsonl")
    records += _read_jsonl(BASE / "data" / "research" / "signals.jsonl")
    queue = build_idea_queue(records, load_strategy(config))
    exports = write_idea_exports(queue, BASE / "data" / "exports")
    summary["ideas"] = {
        "ranked": len(queue),
        "research_ready": sum(1 for item in queue if item["review_status"] == "research_ready"),
        "needs_review": sum(1 for item in queue if item["review_status"] == "needs_review"),
        "exports": {name: str(path.relative_to(BASE)) for name, path in exports.items()},
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
