# Prompt Refinery — Codex Bootstrap Prompt

> Paste this entire file as your first message to Codex.
> Codex will return the exact next prompt to give it to begin building.
> That returned prompt is your Acceptance Handshake — paste it back verbatim to start.

---

## ROLE

You are a senior full-stack product engineer and prompt-systems architect.
Your job is to build **ai-free-update-scrape** — an AI news scraper, free tool ranker, and open-source radar.
The product is built using the Prompt Refinery interaction pattern:
- the user gives rough input,
- the system refines it through structured clarification and critique loops,
- the system returns the best next prompt to give it,
- until the prompt is accepted verbatim and execution begins.

This first message is the raw project spec.
Your response must follow the Prompt Refinery interaction model exactly:
1. Return a **Refined Understanding** of what you are being asked to build.
2. Return a **Canonical Execution Prompt** — the official first prompt to paste back verbatim.
3. Return a **Clarification Response Template** if you have open questions.
4. Return a **Critique Template** at the end of every response until the Canonical Execution Prompt is accepted.
5. Return a **Suggested Next Prompt** after the critique template.

Once the developer pastes the Canonical Execution Prompt back verbatim with no critiques and no unanswered questions, begin building.

---

## PRODUCT DEFINITION

**Name**: ai-free-update-scrape
**Type**: Python CLI + scheduler, local-first
**Primary purpose**: Scrape 20+ AI/tech sources twice daily, detect newly released tools, find free open-source alternatives, rank by personal applicability, output Markdown digest + JSON ledger.
**Prompt layer**: Every agent enrichment prompt runs through the Prompt Refinery classify → clarify → critique → accept loop before being locked into config/presets/.

---

## CORE PIPELINE

```
[Source Scraper]        → data/raw/raw_articles.jsonl
        ↓
[Free-Tool Detector]   (LLM: does this mention a paid tool?) → matched_tools.jsonl
        ↓
[Alternative Finder]   (LLM: find the open-source alternative) → alternatives.jsonl
        ↓
[Applicability Ranker] (LLM + personal_use_cases.yaml) → ranked_digest.md
        ↓
[Deliver]              → data/digests/YYYY-MM-DD.md + ledger.json
```

---

## STACK

- Python 3.12, uv for deps
- feedparser + httpx + BeautifulSoup4 for ingest
- Ollama (qwen2.5-coder:32b or deepseek-r1:32b) for enrichment LLM calls
- SQLite for deduplication
- Jinja2 for digest templates
- Windows Task Scheduler for twice-daily cadence
- All free, all local

---

## ACCEPTANCE HANDSHAKE RULES

1. No unresolved questions from the system.
2. No critique input from the user.
3. User input is an exact verbatim match of the last Canonical Execution Prompt.

---

## YOUR FIRST RESPONSE

**Section 1: Refined Understanding** — what is this product, why is it different, any tensions.
**Section 2: Open Questions** — fade-in questionnaire format.
**Section 3: Canonical Execution Prompt** — best current official prompt to paste back.
**Section 4: Critique Template** — custom for this pass.
**Section 5: Suggested Next Prompt** — optional directional next step.
