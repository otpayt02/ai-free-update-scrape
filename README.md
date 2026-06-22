# ai-free-update-scrape

AI news scraper + free tool ranker + open-source radar.

Scrapes 20+ sources twice daily. Detects new AI tools. Finds free open-source alternatives. Ranks by personal applicability. Outputs a Markdown digest + JSON ledger.

Every input runs through the **Prompt Refinery** methodology before execution.

---

## Quickstart

```bash
uv sync
python -m ai_free_update_scrape.schedule
```

## Folder Map

```
src/ai_free_update_scrape/
  ingest/      ← RSS + HN + GitHub Trending scrapers
  enrich/      ← LLM tool-detector + free-alt finder
  rank/        ← applicability ranker vs personal_use_cases.yaml
  deliver/     ← Markdown digest + JSON ledger writer
config/
  sources.yaml           ← all RSS + scrape sources
  personal_use_cases.yaml← your ranked use cases
  presets/               ← prompt presets per agent step
data/
  raw/       ← .jsonl rolling ingest
  processed/ ← .jsonl enriched
  digests/   ← YYYY-MM-DD.md daily outputs
prompt_library/          ← Prompt Refinery global templates
conversations/           ← Prompt Refinery session logs
```

## Prompt Refinery Integration

This repo uses the [Prompt Refinery](https://github.com/otpayt02/prompt-refinery) methodology.
Every new feature or agent prompt goes through:
`intake → classified → clarified → critiqued → accepted → execution`

See `CODEX_PROMPT.md` to bootstrap a Codex session. See `SPEC.md` for the full interaction model.

---

## MVP Scope (no scope creep)

1. Scrape 20+ sources twice daily
2. LLM pass: detect new tools, find free alternatives, rank by use cases
3. Output Markdown digest + JSON ledger
4. Prompt Refinery loop as enrichment pre-processor

Out of scope: Ollama setup, VSCode config, voice stack, paid SaaS.
