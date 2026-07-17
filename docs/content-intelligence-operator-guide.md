# Content intelligence operator guide

This project collects evidence for video decisions. It does not bypass access controls, predict virality or revenue, approve sources automatically, or publish videos.

## Daily operating loop

1. Discover: permitted RSS feeds remain the active news source set. The Hacker News Firebase API can add novel outbound domains to `data/source_registry.json` as `review_required` candidates.
2. Collect: enabled official APIs and operator-approved imports append normalized records to `data/research/signals.jsonl`.
3. Analyze: the system classifies each record by audience, content pillar, and both short-form and long-form options.
4. Rank: the evidence score combines 72-hour signal velocity, comparable source engagement, and configured offer relevance.
5. Review: the operator verifies source trust, checks the source link, fills data gaps, and chooses an idea.
6. Produce: approved ideas can move into the existing YT Auto workflow. Upload and publish remain locked behind human review.

Run the complete local cycle:

```powershell
python .\run_research.py
```

Run only stored-evidence analysis, with no network collection:

```powershell
python .\run_research.py --ideas-only
```

Open the dashboard:

```powershell
python .\run_dashboard.py
```

Then open `http://127.0.0.1:5052` and use **Ideas** or **Discover**.

## Daily scheduling

The stable Task Scheduler action is:

- Program: the Python executable used for this repository
- Arguments: `run_research.py`
- Start in: `C:\Users\olive\Projects\ai-free-update-scrape`

Choose the run time in Windows Task Scheduler after confirming API quotas. The repository does not register a machine-wide task automatically.

## Audience taxonomy

The five requested audience groups are first-class: solo freelancers/operators, vibe coders, developers, small businesses, and corporate professionals. Creators/educators and everyday productivity users provide explicit cross-audience fallbacks instead of forcing every signal into the wrong group. Keywords are defined in `src/content_intelligence.py` and can be extended without changing the scoring engine.

## Video pillars and formats

The classifier covers AI/tech news, tips and tricks, pain-point solutions, manual-task automation, concept education, tool instructions, systems mindset/motivation, use cases/portfolio showcases, products/affiliates/backend offers, and comparisons/reviews. Every idea carries both `short` and `long` as valid format options; `recommended_format` identifies the better first treatment based on the pillar and evidence depth.

## Pain-point sources

Configured in `config/content_strategy.yaml`:

- Stack Exchange: official questions API; enabled.
- GitHub: official REST Issues API; enabled. A read-only token is optional for higher quotas.
- YouTube comments: YouTube Data API; disabled until `YOUTUBE_API_KEY` and video IDs are configured.
- Reddit: Reddit Data API; disabled until approved OAuth access is configured.
- Product review evidence: operator-approved CSV or JSONL import under `data/research/imports`; direct stealth scraping of AppSumo, Product Hunt, or similar review pages is not implemented.

Author identities are not retained. The content is evidence of a public question, issue, or complaint—not proof that every factual claim inside it is true.

## Source trust gate

`src/research.py` exposes a weighted review rubric:

- permitted API/RSS/export access: 20
- identifiable publisher or accountable organization: 15
- links to primary evidence: 15
- appropriate freshness: 15
- independent corroboration: 15
- visible corrections and update history: 10
- HTTPS: 5
- commercial or affiliate disclosure: 5

A discovered domain receives only the points currently proven. Hacker News discovery proves that the sample URL uses HTTPS; it does not prove permission to collect from the destination or publisher reliability. New domains therefore remain inactive until a human finds a permitted RSS/API path and completes the missing review dimensions.

## Evidence score

The default formula is:

`score = keyword growth velocity * 0.4 + source engagement * 0.3 + monetization intent * 0.3`

The queue keeps each component and its basis visible. Missing data is `null` and named in `data_gaps`; it is not invented. Offer relevance remains zero until real products, services, or affiliate relationships and their keywords are added to `config/content_strategy.yaml`. Configure only offers you can accurately disclose.

## Outputs

- `data/source_registry.json`: permanent source candidates and trust gaps
- `data/research/signals.jsonl`: normalized public pain/demand signals
- `data/exports/content_idea_queue.json`: complete machine-readable queue
- `data/exports/content_idea_queue.csv`: sortable review table
- `data/exports/content_idea_queue.md`: human-readable review queue

The queue is a prioritization aid. YouTube Partner Program eligibility, audience response, monetization timing, affiliate conversions, and sales require separate real-world validation.
