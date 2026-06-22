"""Applicability ranker: scores each enriched article against your use cases."""
import yaml
import json
from pathlib import Path


RANK_PROMPT = """
You are a personal AI tool relevance ranker.
Given this article and list of personal use cases, score how relevant this article is
to each use case on a scale of 0-10.

Article: {title} — {summary}
Detected tool: {tool_name}
Alternatives found: {alternatives}

Use cases:
{use_cases}

Respond as JSON: {{"scores": {{"use_case_id": score, ...}}, "top_score": 0-10, "reason": "..."}}
"""


def rank_article(article: dict, use_cases: list[dict], ollama_model: str = "qwen2.5-coder:32b") -> dict:
    try:
        import ollama
        use_cases_text = "\n".join(
            f"- {uc['id']} (priority {uc['priority']}): {uc['description']}" for uc in use_cases
        )
        prompt = RANK_PROMPT.format(
            title=article.get("title", ""),
            summary=article.get("summary", "")[:300],
            tool_name=article.get("detection", {}).get("tool_name", "N/A"),
            alternatives=json.dumps(article.get("alternatives", [])[:3]),
            use_cases=use_cases_text,
        )
        response = ollama.generate(model=ollama_model, prompt=prompt)
        result = json.loads(response["response"].strip())
        return {**article, "ranking": result}
    except Exception as e:
        return {**article, "ranking": {"top_score": 0, "error": str(e)}}


def load_use_cases(config_path: Path) -> list[dict]:
    with open(config_path) as f:
        return yaml.safe_load(f)["use_cases"]
