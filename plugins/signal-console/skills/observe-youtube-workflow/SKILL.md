---
name: observe-youtube-workflow
description: Observe an operator-performed YouTube or scraper-to-video workflow, capture each visible manual action and decision, classify repeatable steps, and recommend the smallest safe checklist, skill, browser automation, webhook, script, or MCP boundary. Use when the user asks to watch, document, streamline, replay, or automate their YouTube setup, content preparation, review, upload, or reporting workflow.
---

# Observe YouTube Workflow

## Guardrails

- Observe only windows, tabs, files, and accounts the user explicitly places in scope.
- Never inspect passwords, cookies, browser profiles, recovery codes, private messages, or unrelated tabs.
- Do not passively monitor the desktop. Run a bounded observation session with a stated start and stop.
- Do not publish, upload, submit, delete, buy, or change account settings while observing.
- Pause before any sensitive data appears and let the operator complete that step privately.
- Treat every proposed automation as a draft until the operator approves its trigger, inputs, side effects, credentials, and rollback.

## Workflow

1. Define the workflow's start, finish, and success evidence.
2. Ask the operator to perform one normal example while narrating decisions that are not visible.
3. Capture one journal row per action using the schema in `references/observation-schema.md`.
4. Separate mechanical actions from judgment, approvals, exceptions, and sensitive steps.
5. Group repeated mechanical actions into automation candidates.
6. Choose the smallest boundary:
   - checklist for infrequent or changing work;
   - template for repeated content structure;
   - skill for repeatable reasoning and file workflows;
   - browser automation for stable, visible UI steps with no supported API;
   - webhook or API for stable system-to-system events;
   - MCP tool for a reusable, auditable domain action an agent needs.
7. Keep login, claims review, final media review, and public publishing as human gates.
8. Return the observed workflow, time sinks, failure points, proposed boundary, approval requirements, and one testable next improvement.

## Completion Standard

A session is complete only when every proposed automation maps back to observed evidence, the non-goals are explicit, and the operator can inspect the steps before enabling anything.
