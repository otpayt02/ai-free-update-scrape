---
name: thread-context-docs
description: "Generate and maintain a compact, inspectable Markdown record of the current Codex thread: requests, decisions, changes, verification evidence, open work, automation candidates, and inefficiencies. Use when a project needs an operator-readable thread handoff, a recurring AI-managed change queue, or an up-to-date context document after implementation, debugging, browser checks, or manual review."
---

# Thread Context Docs

Maintain `docs/thread-context.md` as the factual handoff for one project thread. Treat the supplied JSON as the source of truth; do not invent events, user requests, test results, or completed work.

## Workflow

1. Read the current project instructions and inspect the active work before recording it.
2. Update a small JSON ledger with the current request, decisions, code changes, browser/manual evidence, open queue, and inefficiencies.
3. Classify every queue item as `automatic`, `approval_required`, or `blocked`.
4. Apply only `automatic` items that are safe, local, and explicitly within the current request. Record what actually happened before marking it applied.
5. Generate the Markdown handoff:

```powershell
.\.venv\Scripts\python.exe .\.agents\skills\thread-context-docs\scripts\generate_thread_context.py --input .\docs\thread-context.json --output .\docs\thread-context.md
```

6. Run the generator after each material update and before handoff. Keep unresolved work in the queue instead of implying it is complete.

## Boundaries

- Do not inspect credentials, private browser state, unrelated projects, or restricted paths.
- Treat a browser check, Playwright trace, manual operator note, and test result as separate evidence types.
- Never auto-apply publishing, credential, external-account, destructive, or user-choice changes. Put them in `approval_required`.
- Keep the document compact. Link to code, endpoints, and artifacts rather than duplicating their full content.

## Resource

- `scripts/generate_thread_context.py` validates the ledger shape and renders the inspectable Markdown document.
