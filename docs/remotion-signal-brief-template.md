# Remotion Signal Brief template

## Selected direction

The **Signal Brief** won over a ticker and a side-by-side tool comparison because it keeps one message per scene, remains readable on a phone, and maps directly to structured scraper fields.

## Input contract

- `source`: visible source label.
- `headline`: the scraped article title.
- `hook`: one short reason to keep watching.
- `context`: the real inputs or evidence behind the workflow.
- `instruction`: the concrete job and destination format.
- `review`: the human verification step.
- `cta`: a low-risk next action.
- `accent`: one muted brand color.

## Prompt template

> Using only the supplied source title, summary, URL, and verified notes, create a five-scene vertical Signal Brief. Scene 1 states one concrete hook. Scene 2 names the real context required. Scene 3 gives one actionable instruction. Scene 4 states the human review gate. Scene 5 gives a low-risk CTA. Keep each main message under 18 words. Do not invent product capabilities, prices, dates, quotes, adoption claims, or outcomes. Return JSON matching the SignalBrief props contract.

## Code rationale

- `sceneFrames` gives every scene the same six-second editing unit.
- `Enter` uses frame-driven interpolation and Bézier easing; CSS animation is avoided because it is not deterministic in a render.
- `Frame` reserves fixed layout slots for the label, main message, supporting text, and progress indicator so text never competes with another block.
- Five `Sequence` elements separate the ideas in time instead of shrinking text to fit one crowded frame.
- `defaultProps` keeps the first filled example editable in Remotion Studio and makes the template reusable by scripts later.
- The palette mirrors the dashboard: neutral charcoal, warm sand, cool blue, and muted green.

## Render

```powershell
cd C:\Users\olive\Projects\ai-free-update-scrape\media\remotion-signal-brief
npm.cmd install
npx.cmd remotion render src\index.ts SignalBrief ..\..\artifacts\remotion\signal-brief-chatgpt-work.mp4
```

The video is a private proof artifact. Review the source, wording, and output before any upload.
