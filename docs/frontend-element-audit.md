# Frontend Element Audit

Every retained element below has a live backend source or action. Decorative
hero content, logo marks, profile chrome, placeholder charts, pie charts, and
inactive navigation were removed.

| Element | Route | Decision or action | Backend source/action | States | Retention |
|---|---|---|---|---|---|
| Compact stat grid | Overview | Assess volume and health | `GET /api/dashboard` | loading, zero, error | Include |
| Pipeline activity chart | Overview | Detect throughput and failures | persisted telemetry events | empty, populated, error | Include |
| Stage volume | Overview | Find pipeline concentration | telemetry summary | empty, populated | Include |
| Recent events | Overview | Identify current activity | `GET /api/events` | empty, populated | Include |
| Run command | Global | Start configured execution | `POST /api/run` | ready, running, error | Include |
| Cancel command | Live run | Stop active child process | `POST /api/run/cancel` | disabled, cancelling, error | Include |
| Execution stream | Live run | Diagnose pipeline behavior | sanitized process output | idle, streaming, completed | Include |
| Category table | Categories | Compare and enable categories | `GET /api/categories` | empty, populated, error | Include |
| Category inspector | Categories | Edit taxonomy and thresholds | `PUT /api/categories` | clean, dirty, saved, error | Include |
| Source table | Sources | Audit source availability | `GET /api/state` | empty, populated, error | Include |
| Source probe | Sources | Verify one source | `POST /api/sources/test` | pending, success, error | Include |
| Results table | Results | Inspect collected articles | `GET /api/results` | empty, populated, error | Include |
| Failure list | Failures | Find failed stages | telemetry status filter | empty, populated | Include |
| Trace/event list | Traces | Correlate run and trace IDs | `GET /api/events` | empty, populated | Include |
| Schedule defaults | Schedules | Inspect scheduler authority | persisted dashboard config | configured, empty | Defer editing until Task Scheduler adapter exists |
| Runtime form | Configuration | Tune working limits | `PUT /api/config` | clean, saved, validation error | Include |
| Credential status | Configuration | Confirm provider readiness | `GET /api/health` | configured, missing | Include |
| Model discovery | Configuration | List authorized remote and running local models | `GET /api/models?provider=all` | missing key, loaded, partial provider error | Include |
| Model selector | Configuration | Choose the runtime provider and model | persisted `selected_provider` and `selected_model` | loading, filtered, selected, unsaved | Include |
| Credential editor | Configuration | Add or replace one Windows user environment key | localhost-only `POST /api/credentials` | missing, configured, validation error | Include |
| Model test | Configuration | Verify the selected provider/model pair | `POST /api/models/test` | pending, success, sanitized error | Include |

## Post-build audit

- All nine navigation items render real persisted information or a working action.
- The Schedules view intentionally exposes its current authority and does not
  pretend to save cadence until a Windows Task Scheduler adapter is implemented.
- No credential characters reach browser responses.
- No chart is shown when telemetry is empty.
- No metric is synthesized from placeholder values.
