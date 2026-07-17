# {{PRODUCT_NAME}} console design template

## Product job

Help {{PRIMARY_USER}} move one {{INPUT_OBJECT}} toward one {{REVIEWABLE_OUTPUT}} without hiding failures or crossing {{APPROVAL_GATE}}.

## Signature

Use a midnight operational canvas with one scarce chromatic signal. The accent identifies the primary action or current selection and is never filler decoration.

## Required tokens

```css
--canvas: #090909;
--surface: #0d0d0e;
--surface-raised: #101012;
--text: #f7f9fa;
--muted: #828384;
--signal: {{ACCENT_HEX}};
--signal-soft: {{ACCENT_SOFT_HEX}};
--ready: #b7c8bb;
--hairline: rgba(247, 249, 250, 0.14);
--radius-panel: 19px;
--radius-control: 8px;
```

## Functional-element rule

Every button navigates, mutates real state, submits a form, expands content, opens a source, or dismisses feedback. Plain text exists only as a heading, label, value, status, necessary instruction, or hierarchy aid. Remove fake KPIs, placeholder actions, decorative pills, empty cards, and empty event handlers.

## Progressive disclosure

Keep the current job visible. Put configuration, traces, optional settings, and long explanations in labeled disclosures. Preserve keyboard focus, reduced motion, responsive navigation, source provenance, and the approval gate.

## Required help surface

Add a Help workspace that documents every global control, navigation target, form action, disclosure, external link, disabled state, and safety boundary in user language.

## Acceptance checklist

- Production build and relevant tests pass.
- Every interactive element has observable behavior.
- Every external claim or selected item retains its source.
- Desktop and mobile navigation remain labeled.
- Publishing or destructive actions are explicitly gated.

