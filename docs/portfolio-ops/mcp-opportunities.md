# MCP opportunity assessment

## Decision

The existing YT Auto MCP surface is justified because its operations recur, have stable inputs, benefit multiple clients, and can remain approval-gated. The new journal and template endpoints should remain a normal application API until another client genuinely needs them.

## Viable tool surface

- `status`: read-only runtime and configuration summary.
- `list_signals`: read-only bounded signal results.
- `create_template`: writes a draft template with source provenance.
- `validate_template`: read-only schema and guardrail check.
- `render_preview`: writes a local review artifact.
- `publish`: excluded until client-owned OAuth, private-draft tests, audit logs, and explicit approval exist.

## Contract

Each write accepts an idempotency key and returns an object id, state, warnings, and audit id. Authentication is local process access now; a remote version requires client-owned authentication, least-privilege scopes, rate limits, and signed logs. Secrets and raw cookies are never tool arguments or log fields.

## Rejected as MCP

Browser click observation is judgment-heavy and session-scoped, so it belongs in the `observe-youtube-workflow` skill with Computer Use or browser control. The scrape and render steps are deterministic, so they stay scripts. A YouTube upload adapter is an external API integration, not automatically an MCP requirement.

