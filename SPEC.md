# Prompt Refinery — Product Spec (ai-free-update-scrape edition)

## One-line definition
A prompt-engineering workspace that converts rough intent into a classified, clarified, critique-ready, reusable prompt pipeline — applied here to every agent step in the ai-free-update-scrape radar.

---

## Product states

```
intake_received
  → classified
  → clarification_needed
  → prompt_draft_returned
  → critique_received
  → prompt_revised
  → ready_for_acceptance
  → accepted_verbatim
  → execution_pipeline_started
```

---

## Conversation numbering

- Conversations: `0000`, `0001`, `0002` ...
- Within conversation:
  - Inputs:    `XXXX.N.0`
  - Responses: `XXXX.N.5`

---

## File organization rules

| Artifact | Location |
|---|---|
| Live conversation log | `conversations/XXXX/XXXX_conversation.md` |
| Individual input turns | `conversations/XXXX/turns/XXXX.N.0_input.md` |
| Individual response turns | `conversations/XXXX/turns/XXXX.N.5_response.md` |
| Clarification Q&A | `conversations/XXXX/clarifications/` AND `clarification_templates/XXXX/` |
| Critique templates | `conversations/XXXX/critiques/` AND `critique_templates/XXXX/` |
| Next step prompts | `conversations/XXXX/next_step_prompts/chosen/` or `ignored/` |
| Canonical prompt attempts | `conversations/XXXX/canonical_prompts/` |
| AI-generated templates | `prompt_library/{family}/` (global) |
| Session log | `session_log/XXXX_session.md` |

---

## Advanced prompt engineering constraints

1. Schema-first outputs — typed objects, not free-form.
2. Router-first classification — classify before generating.
3. Clarification minimization — ask only high-value questions.
4. Critique as first-class workflow — always custom, never generic.
5. Explicit halt conditions — state machine enforced.
6. Versioned templates — `template_v1.md` → `template_v2.md`.
7. No agent loops without stop conditions.
8. Few-shot examples in every template (strong, weak, edge-case).
