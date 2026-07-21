"""
review_queue_routes.py — YT Auto Shorts Review Queue
Flask Blueprint — mount with app.register_blueprint(review_queue_bp)
Reads from data/exports/shorts_plan.csv, persists decisions to data/review_queue.json
"""

from __future__ import annotations
import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request

review_queue_bp = Blueprint("review_queue", __name__, url_prefix="/api/review")

BASE  = Path(__file__).resolve().parents[2]
DATA  = BASE / "data"
QUEUE_PATH  = DATA / "review_queue.json"
SHORTS_CSV  = DATA / "exports" / "shorts_plan.csv"
CAPTURE_DIR = DATA / "captures"


# ── Persistence helpers ───────────────────────────────────────────────────────

def _load_queue() -> dict:
    if not QUEUE_PATH.exists():
        return {"items": [], "updated_at": None}
    try:
        return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"items": [], "updated_at": None}


def _save_queue(queue: dict) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    queue["updated_at"] = datetime.now().isoformat(timespec="seconds")
    QUEUE_PATH.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_shorts() -> list[dict]:
    if not SHORTS_CSV.exists():
        return []
    with SHORTS_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _sync_from_csv(queue: dict) -> tuple[dict, int]:
    """Add any shorts from the plan CSV that are not yet in the queue."""
    existing_ids = {item["id"] for item in queue["items"]}
    shorts = _load_shorts()
    added = 0
    for row in shorts:
        row_id = f"{row.get('day', '')}_{row.get('topic', row.get('title', ''))[:60]}"
        if row_id not in existing_ids:
            queue["items"].append({
                "id": row_id,
                "day": row.get("day", ""),
                "topic": row.get("topic", row.get("title", "Untitled")),
                "hook": row.get("hook", ""),
                "script": row.get("script", row.get("body", "")),
                "tags": row.get("tags", ""),
                "source_url": row.get("url", row.get("source_url", "")),
                "status": "pending",
                "reference_url": "",
                "reference_screenshot": "",
                "capture_file": "",
                "notes": "",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "decided_at": None,
            })
            added += 1
    return queue, added


# ── Routes ────────────────────────────────────────────────────────────────────

@review_queue_bp.get("")
def queue_list():
    """Return all queue items, syncing any new shorts from the CSV first."""
    queue = _load_queue()
    queue, added = _sync_from_csv(queue)
    if added:
        _save_queue(queue)
    status_filter = request.args.get("status")
    items = queue["items"]
    if status_filter:
        items = [i for i in items if i["status"] == status_filter]
    counts = {}
    for item in queue["items"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return jsonify({
        "items": items,
        "counts": counts,
        "total": len(queue["items"]),
        "updated_at": queue.get("updated_at"),
        "csv_exists": SHORTS_CSV.exists(),
    })


@review_queue_bp.post("/sync")
def queue_sync():
    """Force a re-sync from shorts_plan.csv."""
    queue = _load_queue()
    queue, added = _sync_from_csv(queue)
    _save_queue(queue)
    return jsonify({"ok": True, "added": added, "total": len(queue["items"])})


@review_queue_bp.post("/<item_id>/approve")
def approve_item(item_id: str):
    queue = _load_queue()
    for item in queue["items"]:
        if item["id"] == item_id:
            item["status"] = "approved"
            item["decided_at"] = datetime.now().isoformat(timespec="seconds")
            _save_queue(queue)
            return jsonify({"ok": True, "item": item})
    return jsonify({"ok": False, "error": "Item not found"}), 404


@review_queue_bp.post("/<item_id>/reject")
def reject_item(item_id: str):
    queue = _load_queue()
    payload = request.get_json(silent=True) or {}
    for item in queue["items"]:
        if item["id"] == item_id:
            item["status"] = "rejected"
            item["notes"] = str(payload.get("reason", ""))[:500]
            item["decided_at"] = datetime.now().isoformat(timespec="seconds")
            _save_queue(queue)
            return jsonify({"ok": True, "item": item})
    return jsonify({"ok": False, "error": "Item not found"}), 404


@review_queue_bp.put("/<item_id>")
def update_item(item_id: str):
    """Edit hook, script, tags, reference_url, notes inline."""
    queue = _load_queue()
    payload = request.get_json(silent=True) or {}
    allowed = {"hook", "script", "tags", "reference_url", "notes", "status"}
    for item in queue["items"]:
        if item["id"] == item_id:
            for key in allowed:
                if key in payload:
                    item[key] = str(payload[key])[:2000]
            if payload.get("status") in ("approved", "rejected", "pending", "editing"):
                item["decided_at"] = datetime.now().isoformat(timespec="seconds")
            _save_queue(queue)
            return jsonify({"ok": True, "item": item})
    return jsonify({"ok": False, "error": "Item not found"}), 404


@review_queue_bp.post("/<item_id>/request-capture")
def request_capture(item_id: str):
    """
    Write a capture_brief.md into data/captures/<item_id>/
    and set status to awaiting_capture.
    """
    queue = _load_queue()
    for item in queue["items"]:
        if item["id"] == item_id:
            brief_dir = CAPTURE_DIR / item_id
            brief_dir.mkdir(parents=True, exist_ok=True)
            brief = f"""# Capture Brief — {item["topic"]}

## What to record
Record a 15-30 second screen capture showing a tool, workflow, or demo relevant to:

**Topic:** {item["topic"]}
**Hook:** {item["hook"]}
**Script:** {item["script"]}

## Recording checklist
- [ ] OBS Studio open, output set to MP4, 1080x1920 (portrait) or 1920x1080 landscape
- [ ] Private/sensitive info hidden or mocked
- [ ] Clean browser window (bookmarks hidden, zoom 90-100%)
- [ ] Demo or tool visible and running
- [ ] Record 15-30 seconds

## Drop your recording here
After recording, drop the MP4 file into:
  data/captures/{item_id}/

File will be auto-detected and status will flip to CAPTURE_READY.

## Reference
{item.get("reference_url", "No reference URL set")}
"""
            (brief_dir / "capture_brief.md").write_text(brief, encoding="utf-8")
            item["status"] = "awaiting_capture"
            item["capture_file"] = ""
            _save_queue(queue)
            return jsonify({
                "ok": True,
                "brief_path": str(brief_dir / "capture_brief.md"),
                "drop_folder": str(brief_dir),
                "item": item,
            })
    return jsonify({"ok": False, "error": "Item not found"}), 404


@review_queue_bp.get("/<item_id>/capture-status")
def capture_status(item_id: str):
    """Check if a capture MP4 has been dropped into the batch folder."""
    brief_dir = CAPTURE_DIR / item_id
    mp4_files = list(brief_dir.glob("*.mp4")) if brief_dir.exists() else []
    if mp4_files:
        queue = _load_queue()
        for item in queue["items"]:
            if item["id"] == item_id and item["status"] == "awaiting_capture":
                item["status"] = "capture_ready"
                item["capture_file"] = mp4_files[0].name
                _save_queue(queue)
        return jsonify({"ready": True, "file": mp4_files[0].name})
    return jsonify({"ready": False, "file": None})


@review_queue_bp.get("/stats")
def queue_stats():
    queue = _load_queue()
    counts: dict[str, int] = {}
    for item in queue["items"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return jsonify({
        "counts": counts,
        "total": len(queue["items"]),
        "approved": counts.get("approved", 0),
        "pending": counts.get("pending", 0),
        "rejected": counts.get("rejected", 0),
        "awaiting_capture": counts.get("awaiting_capture", 0),
        "capture_ready": counts.get("capture_ready", 0),
    })
