# Signal Console design contract

This file is the implementation source of truth for the `ai-free-update-scrape` interface. It adapts the submitted MagicPath Signal Console component to the visual rules in `C:\Users\olive\Projects\DESIGN.md` without changing the application's runtime contracts.

## Product job

Help one operator move one traceable AI-news signal toward one reviewable Short without hiding failures or crossing the publishing approval gate.

## Signature

The interface is a midnight operations console with one scarce violet beacon. Violet marks the primary action or current selection; it is not ambient decoration.

## Tokens

```css
--canvas: #090909;
--surface: #0d0d0e;
--surface-raised: #101012;
--text: #f7f9fa;
--muted: #828384;
--signal: #af50ff;
--signal-soft: #e1bdff;
--ready: #b7c8bb;
--hairline: rgba(247, 249, 250, 0.14);
--font-body: "DM Sans", "Inter", system-ui, sans-serif;
--font-utility: "IBM Plex Mono", ui-monospace, monospace;
--radius-panel: 19px;
--radius-control: 8px;
```

## Layout

The app uses one sticky frosted header and one bordered console frame. Desktop navigation is horizontal. At narrow widths it becomes a second scrollable header row; it never turns into an unlabeled icon rail. Each workspace shows one primary job and progressively discloses secondary information.

## Interaction contract

- Every button must call a handler, submit a controlled form, navigate, open a source, expand content, or dismiss state.
- Disabled buttons must communicate a real unavailable state.
- Plain text may exist only as a heading, label, value, status, instruction required to complete a task, or visual hierarchy aid.
- Do not add fake KPIs, decorative pills, empty cards, placeholder actions, or controls with empty handlers.
- Keep keyboard focus visible and respect reduced-motion preferences.
- Keep `Publish` locked until a separately documented approval workflow exists.

## Workspaces

- **Signals:** choose a ranked source, inspect evidence, open its source, or build a template.
- **Workflow:** expand production stages and map journal entries to automation boundaries.
- **Journal:** save a real manual action, stage, and automation-candidate decision.
- **Templates:** edit and save a source-linked content draft; advanced render settings stay collapsed.
- **System:** inspect runtime state and invoke only enabled YT Auto tools.
- **Help:** explain the effect of every visible control and the safe operating boundary.

## Copy rules

Use short active verbs: `Refresh`, `New scrape`, `Open source`, `Build template`, `Save step`, and `Save draft template`. Remove prose that does not help the operator decide or act. Errors name what failed; empty states name the next available action.

## Code mapping

`frontend/src/App.tsx` owns data contracts, state, navigation, controls, and help content. `frontend/src/styles.css` owns tokens, layout, responsive behavior, focus, and reduced motion. `src/web/app.py` remains the runtime and persistence boundary.

## Acceptance checklist

1. Production build passes.
2. Existing API and workspace tests pass.
3. Every visible button has a real handler or link target.
4. Navigation works at desktop and mobile widths.
5. Help names every control category present in the app.
6. Scraping, journaling, template saving, source opening, refresh, disclosures, notices, and enabled system tools remain functional.

