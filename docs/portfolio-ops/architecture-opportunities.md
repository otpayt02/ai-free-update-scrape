# Architecture opportunities

## Keep now

Keep Flask as the local orchestration boundary, React as the operator surface, file-backed workspace records for inspectability, and Remotion as a parameterized renderer.

## Extract later

Extract a render worker only when renders need queuing or concurrency. Extract a database only when multiple operators or conflict resolution become real requirements. Do not introduce either for a single-user Fiverr demo.

## Observability

Record `run_id`, source, step, start/end time, result count, error category, template id, render path, and approval state. Never log tokens, cookies, OAuth payloads, or full private source text.

