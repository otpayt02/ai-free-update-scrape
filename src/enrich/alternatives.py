"""LLM-based free alternative finder: given a paid tool, find the OSS replacement."""

from ..providers import generate_json


ALT_PROMPT = """
You are a free/open-source software expert. Given this paid or proprietary AI tool,
list the best free open-source alternatives available as of 2026.

Tool name: {tool_name}
Context: {summary}

Respond as JSON only:
{{"alternatives": [{{"name": "...", "github": "...", "why": "..."}}]}}
"""


def find_alternatives(article: dict, model: str, provider: str = "nvidia") -> dict:
    """Find free alternatives for a detected paid tool."""
    tool_name = article.get("detection", {}).get("tool_name", "")
    if not tool_name:
        return {**article, "alternatives": []}
    try:
        prompt = ALT_PROMPT.format(
            tool_name=tool_name,
            summary=article.get("summary", "")[:300],
        )
        result = generate_json(provider, model, prompt)
        return {**article, "alternatives": result.get("alternatives", [])}
    except Exception as e:
        return {**article, "alternatives": [], "alt_error": str(e)}
