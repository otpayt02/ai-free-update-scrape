# Telemetry Schema

Telemetry is append-only JSONL at `data/telemetry/events.jsonl`.

Required fields:

- `event_id`: unique event identifier; never used as a metric label.
- `run_id`: correlates one scrape execution; never used as a metric label.
- `trace_id`: correlates related operations; never used as a metric label.
- `timestamp`: Unix time in seconds.
- `stage`: bounded pipeline stage name.
- `status`: bounded value such as `ok`, `event`, or `error`.

Optional fields include `message`, `exit_code`, `source_id`, `category_id`,
`duration_ms`, and a redacted configuration snapshot. URLs, titles, exception
messages, credentials, run IDs, and trace IDs are not Prometheus-style labels.

