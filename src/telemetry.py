"""Low-cardinality local telemetry for scrape runs and pipeline events."""

from __future__ import annotations

import json
import time
import uuid
from collections import Counter
from pathlib import Path


class TelemetryStore:
    """Append structured run events and build dashboard-safe summaries."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, run_id: str, stage: str, status: str, **fields: object) -> dict:
        event = {
            "event_id": str(uuid.uuid4()), "run_id": run_id, "trace_id": fields.pop("trace_id", str(uuid.uuid4())),
            "timestamp": time.time(), "stage": stage, "status": status, **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def read(self, limit: int = 1000) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def summary(self) -> dict:
        events = self.read(5000)
        stages = Counter(event.get("stage", "unknown") for event in events)
        statuses = Counter(event.get("status", "unknown") for event in events)
        runs = {event.get("run_id") for event in events if event.get("run_id")}
        return {"events": len(events), "runs": len(runs), "stages": stages, "statuses": statuses}

