# Prompt Family: product_spec

## Purpose
Define product, MVP, architecture from rough intent.

## Template

```
You are a senior product engineer. Convert the following rough intent into:
1. One-line product definition.
2. MVP scope (3-5 bullets, strict — label anything out of scope).
3. Folder/file structure.
4. Tech stack (all free/open-source unless stated).
5. Build order (numbered).

Rough intent:
{input}
```

## Strong example
> Input: "I want to scrape AI news and find free alternatives."
> Output: Full spec with folder map, pyproject.toml stack, 10-step build order.

## Weak example
> Input: One word ("scraper").
> Output: Too vague. Prompt Refinery will trigger clarification before generating.
