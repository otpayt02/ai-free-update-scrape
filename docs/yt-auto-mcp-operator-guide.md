# YT Auto MCP Control Center

## What this proves

This local control center connects a production-shaped React dashboard to the existing `yt_auto` Python pipeline through a guarded JSON-RPC tool interface. It demonstrates repository discovery, typed tool schemas, batch selection, evidence-first QA, media validation, upload-package validation, and a deliberately locked publishing boundary.

The demo does not claim live YouTube publishing. The publish tool appears in the registry so a buyer can see the intended boundary, but it is disabled until a separate human-approved workflow is designed and configured.

## Run the demo

```powershell
cd C:\Users\olive\Projects\ai-free-update-scrape
.\.venv\Scripts\python.exe run_dashboard.py
```

Open `http://127.0.0.1:5052`, choose **YT Auto MCP**, and run **yt_auto_status**. Run **yt_auto_qa_batch** only on a batch produced by the current pipeline schema; older fixtures may correctly fail when required artifacts are absent.

## MCP-style endpoint

The local JSON-RPC endpoint is `POST http://127.0.0.1:5052/mcp` and supports:

- `initialize` to negotiate server information and capabilities.
- `tools/list` to return tool names, descriptions, input schemas, and risk annotations.
- `tools/call` to execute an allowlisted tool with validated arguments.

Example tool-list request:

```powershell
$body = @{ jsonrpc = '2.0'; id = 1; method = 'tools/list' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:5052/mcp -Method Post -ContentType 'application/json' -Body $body
```

Example QA request:

```powershell
$body = @{
  jsonrpc = '2.0'
  id = 2
  method = 'tools/call'
  params = @{ name = 'yt_auto_qa_batch'; arguments = @{ batch_id = 'batch_demo_001' } }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://127.0.0.1:5052/mcp -Method Post -ContentType 'application/json' -Body $body
```

## Safety model

- The server binds to localhost and rejects tool calls from non-local addresses.
- Tool names come from a fixed registry; arbitrary shell commands are impossible through this API.
- Batch identifiers accept only letters, numbers, underscores, and hyphens.
- API keys and environment secrets are never returned.
- `publish-batch` is represented but disabled.
- The bridge invokes `yt_auto` in its own repository and does not rewrite its source.

## Code map and rationale

- `src/yt_auto_mcp.py`: owns the tool registry, validates arguments, runs allowlisted CLI commands, reports repository state, and translates JSON-RPC requests. Each helper has one responsibility so the security boundary stays auditable.
- `src/web/app.py`: exposes the UI-facing overview/tool routes and the `/mcp` endpoint. Localhost checks sit at the HTTP boundary before any command can run.
- `frontend/src/App.tsx`: adds the YT Auto MCP workspace, tool cards, batch selector, evidence console, and guardrail/dependency status.
- `frontend/src/overrides.css`: adds the responsive control-center layout and status styling without changing the existing design system.
- `tests/test_control_center.py`: verifies discovery, initialization, tool listing, the publish lock, and batch-ID traversal rejection.

## Extension points

Recommended next integrations, added only when a client needs them:

1. GitHub webhook: convert approved issues labeled `content-batch` into dry-run topic batches. Verify webhook signatures and require a second approval before renders.
2. YouTube Data API: upload private drafts only, never public videos by default. Requires the client's OAuth consent and channel access.
3. Google Drive: deliver approved packages into a client-owned folder and return share links.
4. Slack or Teams: send QA summaries and approval cards; keep execution behind signed callbacks.
5. Sentry: capture production exceptions if this control center is deployed beyond localhost.

## What was learned

This feature demonstrates how to wrap an existing CLI as agent-friendly tools without weakening its original safety contract. The core skills are JSON-RPC design, command allowlisting, path validation, subprocess isolation, React operational UI design, and evidence-based automation.

## Paste-ready next prompts

**Add GitHub intake**

> Add a signed GitHub webhook receiver to the YT Auto MCP Control Center. Accept only issues labeled `content-batch`, store the payload locally, show a preview in the dashboard, and require explicit operator approval before creating any yt_auto artifacts. Do not publish, commit, or push.

**Add private-draft YouTube delivery**

> Design the smallest YouTube Data API integration for uploading an already-approved MP4 as a private draft. Keep OAuth tokens out of the repo, add a dry-run mode, show the exact metadata before upload, and require a typed confirmation phrase. Do not make videos public.

**Package for a Fiverr client**

> Turn the current YT Auto MCP Control Center into a reusable client starter kit with an environment checklist, configuration template, sample fixture batch, acceptance tests, and a sanitized handoff ZIP. Preserve localhost-first and human approval guardrails.
