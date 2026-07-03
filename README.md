# ai-free-update-scrape

AI news scraper + free tool ranker + open-source radar.

Scrapes RSS, HN, GitHub Trending, Reddit JSON, and arXiv sources. Detects new AI tools. Finds free/open-source alternatives. Ranks by personal applicability. Outputs a Markdown digest, JSON ledger, Google Sheets-friendly CSV exports, and a 60-day YouTube Shorts plan.

---

## Quickstart

```bash
uv sync
python run.py
```

## Folder Map

```
src/ai_free_update_scrape/
  ingest/      ← RSS + HN + GitHub Trending + arXiv + Reddit scrapers
  enrich/      ← LLM tool-detector + free-alt finder
  rank/        ← applicability ranker vs personal_use_cases.yaml
  plan/        ← Shorts calendar generation
  export/      ← CSV + dashboard writers
  deliver/     ← Markdown digest + JSON ledger writer
config/
  sources.yaml           ← all RSS + scrape sources
  personal_use_cases.yaml← your ranked use cases
  presets/               ← prompt presets per agent step
data/
  raw/       ← .jsonl rolling ingest
  processed/ ← .jsonl enriched
  digests/   ← YYYY-MM-DD.md daily outputs
  exports/   ← CSVs and local dashboard
```

## Outputs

- `data/digests/YYYY-MM-DD.md` for the daily readout
- `data/exports/articles_sheet.csv` for Google Sheets import
- `data/exports/shorts_plan.csv` for a 60-day Shorts calendar
- `data/exports/shorts_plan.md` for quick human review
- `data/exports/dashboard.html` for a local landing page
- `data/exports/dashboard.xlsx` for a native Sheets import if needed

## Local Dashboard

```bash
python run_dashboard.py
```

Open `http://127.0.0.1:5052` in Chrome or any browser.

The control center can save run limits, enable or disable individual sources,
launch a scrape in the background, stream its console output, and inspect the
latest selected articles and Shorts queue. Dashboard settings are stored in
`config/dashboard.json`; source changes are stored in `config/sources.yaml`.

The Configuration tab discovers models from configured NVIDIA, OpenRouter,
Gemini, Featherless, and OpenAI accounts, plus running LM Studio, vLLM,
llama.cpp, or Ollama-compatible local servers. API keys entered in the local
dashboard are written to the current Windows user's environment and are never
returned to the browser after submission.

---

## MVP Scope

1. Scrape AI-related news sources three times a day or on demand
2. Rank free tools, open-source alternatives, model releases, agents, integrations, and policy updates
3. Export sheet-ready rows and a Shorts plan
4. Keep everything local-first and free-tier compatible

Out of scope: Google Sheets API auth, Remotion rendering, paid SaaS integrations.
