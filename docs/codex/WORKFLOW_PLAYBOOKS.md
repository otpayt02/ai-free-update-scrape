# Workflow playbooks

## Source-cycle recovery

- **Trigger:** automatic discovery returns zero ready sources.
- **Outcome:** preserve the prior active manifest, archive every candidate rule, and show the exact rejection reason.
- **Inputs:** enabled categories, curated source-specific RSS catalog, HTTP response, robots policy, content type.
- **Steps:** discover diverse candidates; probe each; archive rules; append audit entries; replace active sources only when one or more candidates are ready.
- **Owner:** operator approves any catalog change; the source cycle enforces access rules.
- **Bottleneck:** a single search proxy can reject every candidate under one robots policy.
- **Optimized version:** independent source-specific RSS feeds, re-probed on every cycle.
- **Verification:** source-cycle tests plus a live archived manifest with at least one ready rule.
- **Rollback:** zero ready candidates leaves `config/sources.yaml` unchanged.
- **Privacy/cost/approval:** public permitted feeds only; no credentialed sources; no bypass of publisher restrictions.
- **Video-intent source lanes:** start with the intended video category, choose a linked RSS candidate or official API, re-probe feeds before activation, and retain restrictions in the lane parameters. Reddit remains official API-only; no direct page scraping or access-control workaround is an available path.

## Daily content research and idea review

- **Trigger:** the scheduled daily research window or an operator request for current video candidates.
- **Outcome:** collect permitted public signals, stage novel domains, rebuild the evidence-ranked short/long-form queue, and leave every idea unpublished.
- **Inputs:** `config/content_strategy.yaml`, processed articles, official API responses, approved review exports, current offers/affiliates, and source trust reviews.
- **Steps:** run `python run_research.py`; inspect collector statuses; review new registry domains; open Ideas; filter by audience/pillar/format; verify source and data gaps; approve an idea only after evidence review.
- **Tools:** RSS and HN Firebase API for discovery; Stack Exchange/GitHub/YouTube/Reddit official APIs; local CSV/JSONL imports; deterministic classifier and scoring engine.
- **Owner:** the operator controls credentials, source activation, offer disclosure, idea approval, upload, and publishing.
- **Bottleneck:** source trust and comparable engagement/history are often missing; a high score does not remove those gaps.
- **Optimized version:** one bounded command creates durable source, signal, and idea artifacts, while the dashboard exposes component bases and review gates.
- **Verification:** targeted pytest suite, Ruff, frontend production build, bounded live collector counts, registry candidate count, and rendered Ideas route.
- **Rollback:** disable collectors in `config/content_strategy.yaml`; use `--ideas-only`; do not activate review candidates; existing active RSS remains unchanged.
- **Privacy/cost/approval:** do not retain author identities or private/customer data; respect quotas and terms; no stealth scraping; no automatic outreach, upload, publishing, or offer claims.
