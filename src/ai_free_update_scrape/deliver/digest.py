"""Digest writer: outputs YYYY-MM-DD.md and appends to ledger.json."""
import json
from datetime import date
from pathlib import Path


DIGEST_TEMPLATE = """# AI Free Update Scrape — {date}

Generated: {date} | Sources scraped: {source_count} | New tools detected: {tool_count}

---

## Top Picks (ranked by your use cases)

{top_picks}

---

## All Detected Tools

{all_tools}

---

## Free Alternatives Found

{alternatives}
"""


def write_digest(ranked_articles: list[dict], digests_dir: Path, ledger_path: Path) -> Path:
    today = date.today().isoformat()
    digest_path = digests_dir / f"{today}.md"

    # Sort by top_score descending
    sorted_articles = sorted(
        ranked_articles,
        key=lambda a: a.get("ranking", {}).get("top_score", 0),
        reverse=True,
    )

    top_picks = ""
    all_tools = ""
    alternatives_section = ""
    tool_count = 0

    for a in sorted_articles[:20]:
        detection = a.get("detection", {})
        ranking = a.get("ranking", {})
        alts = a.get("alternatives", [])

        if detection.get("new_tool"):
            tool_count += 1
            tool_name = detection.get("tool_name", "Unknown")
            score = ranking.get("top_score", 0)
            reason = ranking.get("reason", "")
            url = a.get("url", "")

            entry = f"### [{a.get('title', tool_name)}]({url})\n"
            entry += f"**Tool**: {tool_name} | **Score**: {score}/10 | **Type**: {detection.get('type', '?')}\n"
            entry += f"**Why it matters**: {reason}\n\n"

            if score >= 7:
                top_picks += entry
            all_tools += entry

            if alts:
                alternatives_section += f"**{tool_name}** free alternatives:\n"
                for alt in alts[:3]:
                    alternatives_section += f"- [{alt.get('name')}]({alt.get('github', '#')}) — {alt.get('why', '')}\n"
                alternatives_section += "\n"

    digest = DIGEST_TEMPLATE.format(
        date=today,
        source_count=len(set(a.get("source", "") for a in sorted_articles)),
        tool_count=tool_count,
        top_picks=top_picks or "_No high-scoring tools today._",
        all_tools=all_tools or "_No new tools detected._",
        alternatives=alternatives_section or "_No paid tools detected — no alternatives needed._",
    )

    digests_dir.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(digest)

    # Append to ledger
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a") as f:
        f.write(json.dumps({"date": today, "digest_path": str(digest_path), "tool_count": tool_count}) + "\n")

    return digest_path
