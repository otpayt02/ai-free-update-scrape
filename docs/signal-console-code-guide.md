# Signal Console code guide

## How the code is organized

`src/web/app.py` owns the HTTP boundary. The workspace helpers load and atomically replace a small JSON document; the three workspace routes expose read, journal-write, and template-write operations. The result route applies the same curated selection rule as the scrape session so the UI does not drown the operator in raw feed volume. Repeated validation and response lines follow one pattern and are not restated individually.

`frontend/src/App.tsx` owns operator state and progressive disclosure. Its types document the server contracts; fetch helpers keep error handling consistent; navigation selects one job at a time; the signal view drives the current selection; workflow, journal, template, and system views reveal details only when requested. Buttons always call a handler or open a real source. Repeated JSX rows use the same rendering rule and are explained once here.

`frontend/src/styles.css` defines the complete visual system. Root variables are the muted warm neutral, cool blue, and status green palette. Layout rules establish the rail, focus pane, and responsive collapse; component rules style controls and disclosures; media queries convert the console to a single-column mobile flow. Repeated declarations apply the same spacing, type, and interaction tokens.

`media/remotion-signal-brief/src/SignalBriefVideo.tsx` declares reusable content props, frame-safe animation helpers, five timed scenes, and the filled default composition. All motion derives from the current frame, making render output deterministic.

## What was learned

The highest-value automation target is not "make videos automatically." It is the repeated handoff between a selected source, a structured template, and a review render. Journaling tiny steps first makes that boundary observable and reduces the chance of automating a fragile exception.

## Paste-ready next prompts

1. `Observe one complete YouTube Studio upload as a bounded session. Log each action, input, decision, wait, and exception. Do not publish or expose credentials. Return the top three automation candidates with confidence and risk.`
2. `Connect the selected Signal Console template to the Remotion SignalBriefVideo props, add a preview-render button, and stop at a local MP4. Verify the exact browser flow and rendered artifact.`
3. `Add a signed GitHub webhook that creates draft content-intake records only. Include signature verification, replay protection, idempotency, structured logs, tests, and no publishing.`

Context reiteration: this is a local-first AI signal-to-video console. Sources remain traceable, rendering is reviewable, and publishing stays locked behind explicit human approval.

