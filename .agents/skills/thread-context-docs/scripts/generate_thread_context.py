"""Render a factual, operator-readable context document from a JSON ledger."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


SECTIONS = (
    ("requests", "Requests and decisions"),
    ("changes", "Changes made"),
    ("evidence", "Verification evidence"),
    ("queue", "Open queue"),
    ("inefficiencies", "Inefficiencies and follow-ups"),
)


def bullet(item: object) -> str:
    if isinstance(item, str):
        return f"- {item}"
    if isinstance(item, dict):
        title = str(item.get("title") or item.get("item") or "Untitled")
        detail = str(item.get("detail") or item.get("status") or "")
        mode = str(item.get("mode") or "")
        suffix = " · ".join(part for part in (mode, detail) if part)
        return f"- **{title}**" + (f" — {suffix}" if suffix else "")
    raise ValueError("Ledger entries must be strings or objects")


def render(payload: dict) -> str:
    title = str(payload.get("title") or "Thread context")
    lines = [f"# {title}", "", f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}", ""]
    for key, heading in SECTIONS:
        lines.extend((f"## {heading}", ""))
        entries = payload.get(key, [])
        if not isinstance(entries, list):
            raise ValueError(f"{key} must be a list")
        lines.extend([bullet(entry) for entry in entries] or ["- None recorded."])
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("The ledger root must be an object")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
