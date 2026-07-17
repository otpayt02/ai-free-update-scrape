# Observation schema

Record one row per visible action:

| Field | Meaning |
| --- | --- |
| sequence | Action order |
| stage | discover, select, template, render, approve, publish, or observe |
| action | What the operator did |
| input | Visible non-sensitive input |
| output | Visible result or evidence |
| decision | Human judgment, if any |
| repeatable | yes, no, or unknown |
| sensitivity | public, internal, credential, or personal |
| failure mode | What could go wrong |
| candidate | checklist, template, skill, browser, webhook, API, MCP, or none |
| approval gate | Required human confirmation |
