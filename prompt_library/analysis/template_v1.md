# Prompt Family: analysis

## Purpose
Break down existing material — articles, codebases, specs, transcripts.

## Template

```
You are an expert analyst. Given the following {material_type}, produce:
1. A 3-sentence summary.
2. Key entities/concepts (bulleted).
3. Tensions or open questions.
4. Recommended next action.

Material:
{content}
```

## Strong example
> Input: A 2000-word arxiv abstract on MoE routing.
> Output: Clean summary, 6 key concepts, 2 open questions, recommends pulling the full paper.

## Weak example
> Input: Vague article title only.
> Output: Hallucinated summary. Add `in:file` constraint.

## Edge case
> Input: Multi-language content. Add `Respond in English regardless of input language.`
