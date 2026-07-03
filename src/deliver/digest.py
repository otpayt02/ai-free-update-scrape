"""Digest writer: outputs YYYY-MM-DD.md and appends to ledger.jsonl."""
import json
from datetime import date
from pathlib import Path


DIGEST_TEMPLATE = """# AI Free Update Scrape — {date}

Generated: {date} | Mode: {mode} | Sources: {source_count} | Articles: {article_count}

---

## Top Picks

{top_picks}

---

## All Articles

{all_tools}

---

## Free Alternatives Found

{alternatives}
"""


def write_digest(
    ranked_articles: list[dict],
    digests_dir: Path,
    ledger_path: Path,
    llm_mode: bool = False,
) -> Path:
    today = date.today().isoformat()
    digest_path = digests_dir / f"{today}.md"

    sorted_articles = sorted(
        ranked_articles,
        key=lambda a: a.get("ranking", {}).get("top_score", 0),
        reverse=True,
    )

    top_picks = ""
    all_tools = ""
    alternatives_section = ""
    tool_count = 0

    for a in sorted_articles[:50]:
        detection = a.get("detection", {})
        ranking = a.get("ranking", {})
        alts = a.get("alternatives", [])

        if not detection.get("new_tool"):
            continue

        tool_count += 1
        tool_name = detection.get("tool_name") or a.get("title", "Unknown")
        score = ranking.get("top_score", 0)
        reason = ranking.get("reason", "")
        url = a.get("url", "")
        source = a.get("source", "")
        published = a.get("published", "")[:10] if a.get("published") else ""
        summary = a.get("summary", "")[:200].replace("\n", " ")

        entry = f"### [{tool_name}]({url})\n"
        entry += f"**Source**: {source} | **Date**: {published} | **Score**: {score}/10\n"
        if not llm_mode:
            entry += f"**Summary**: {summary}...\n\n"
        else:
            entry += f"**Type**: {detection.get('type', '?')} | **Why it matters**: {reason}\n\n"

        if score >= 7:
            top_picks += entry
        all_tools += entry

        if alts:
            alternatives_section += f"**{tool_name}** free alternatives:\n"
            for alt in alts[:3]:
                alternatives_section += f"- [{alt.get('name')}]({alt.get('github', '#')}) — {alt.get('why', '')}\n"
            alternatives_section += "\n"

    mode_label = "NVIDIA-enriched" if llm_mode else "Deterministic scoring"

    digest = DIGEST_TEMPLATE.format(
        date=today,
        mode=mode_label,
        source_count=len(set(a.get("source", "") for a in sorted_articles)),
        article_count=tool_count,
        top_picks=top_picks or "_No high-scoring articles today._",
        all_tools=all_tools or "_No articles scraped — check sources.yaml and your network._",
        alternatives=alternatives_section or ("_Configure NVIDIA enrichment for alternative detection._" if not llm_mode else "_No paid tools detected._"),
    )

    digests_dir.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(digest, encoding="utf-8")

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a") as f:
        f.write(json.dumps({
            "date": today,
            "digest_path": str(digest_path),
            "article_count": tool_count,
            "llm_mode": llm_mode,
        }) + "\n")

    return digest_path
