"""Guarded MCP-style adapter for the neighboring yt_auto repository."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


YT_AUTO_ROOT = Path(os.environ.get("YT_AUTO_REPO", r"C:\Users\olive\Projects\yt_auto")).resolve()
YT_AUTO_RUNS = YT_AUTO_ROOT / "runs"


@dataclass(frozen=True)
class Tool:
    name: str
    command: str | None
    description: str
    risk: str = "safe"
    enabled: bool = True

    def as_mcp(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {"batch_id": {"type": "string", "minLength": 1}},
                "required": [] if self.command is None else ["batch_id"],
                "additionalProperties": False,
            },
            "annotations": {"risk": self.risk, "enabled": self.enabled},
        }


TOOLS = {
    tool.name: tool
    for tool in (
        Tool("yt_auto_status", None, "Inspect repository health, available batches, and required local tools."),
        Tool("yt_auto_qa_batch", "qa-batch", "Run schema, provenance, metadata, and approval-gate QA."),
        Tool("yt_auto_validate_media", "validate-media", "Validate MP4, audio, motion, and media-manifest evidence."),
        Tool("yt_auto_validate_upload_packages", "validate-upload-packages", "Check manual-upload packages without publishing."),
        Tool("yt_auto_render_preview", "render-preview", "Render review media for an existing batch.", "writes_artifacts"),
        Tool("yt_auto_publish_batch", "publish-batch", "Publishing remains locked behind explicit human approval.", "blocked", False),
    )
}


def _safe_batch_id(value: Any) -> str:
    batch_id = str(value or "").strip()
    if not batch_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for character in batch_id):
        raise ValueError("batch_id may contain only letters, numbers, underscores, and hyphens")
    return batch_id


def _command_available(name: str) -> bool:
    return bool(subprocess.run([name, "-version"], capture_output=True, text=True, timeout=4, check=False).returncode == 0)


def status() -> dict[str, Any]:
    batches = []
    if YT_AUTO_RUNS.exists():
        for path in sorted(YT_AUTO_RUNS.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
            if not path.is_dir():
                continue
            artifacts = [item.name for item in path.iterdir() if item.is_file()]
            batches.append({
                "batch_id": path.name,
                "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                "artifact_count": len(artifacts),
                "artifacts": artifacts[:12],
            })
    return {
        "connected": (YT_AUTO_ROOT / "src" / "yt_auto" / "cli.py").exists(),
        "repo_path": str(YT_AUTO_ROOT),
        "run_root": str(YT_AUTO_RUNS),
        "batch_count": len(batches),
        "batches": batches[:20],
        "dependencies": {"python": bool(sys.executable), "ffmpeg": _command_available("ffmpeg"), "ffprobe": _command_available("ffprobe")},
        "guardrails": ["Localhost only", "Allowlisted commands", "Validated batch identifiers", "Publishing disabled", "No secrets returned"],
    }


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    tool = TOOLS.get(name)
    if tool is None:
        raise ValueError(f"Unknown tool: {name}")
    if not tool.enabled:
        raise PermissionError("This tool is locked. Publishing requires a separate operator-approved workflow.")
    if tool.command is None:
        return status()
    batch_id = _safe_batch_id((arguments or {}).get("batch_id"))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(YT_AUTO_ROOT / "src")
    process = subprocess.run(
        [sys.executable, "-m", "yt_auto.cli", tool.command, "--batch-id", batch_id],
        cwd=YT_AUTO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    output = (process.stdout or process.stderr).strip()
    try:
        payload: Any = json.loads(output)
    except json.JSONDecodeError:
        payload = {"output": output[-12000:]}
    return {"ok": process.returncode == 0, "exit_code": process.returncode, "tool": name, "batch_id": batch_id, "result": payload}


def handle_jsonrpc(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    request_id = payload.get("id")
    method = payload.get("method")
    try:
        if method == "initialize":
            result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "yt-auto-control-center", "version": "0.1.0"}}
        elif method == "tools/list":
            result = {"tools": [tool.as_mcp() for tool in TOOLS.values()]}
        elif method == "tools/call":
            params = payload.get("params") or {}
            tool_result = call_tool(str(params.get("name", "")), params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(tool_result, indent=2)}], "isError": not tool_result.get("ok", True)}
        else:
            raise ValueError(f"Unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}, 200
    except PermissionError as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32001, "message": str(exc)}}, 403
    except (ValueError, subprocess.TimeoutExpired) as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}}, 400
