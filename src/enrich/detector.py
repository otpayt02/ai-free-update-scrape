"""LLM-based tool detector: does this article mention a new/paid AI tool?"""

from ..providers import generate_json


DETECT_PROMPT = """
You are an AI tool detector. Given the article title and summary below, answer:
1. Does this article mention a new AI tool, model, or service released in the last 7 days? (yes/no)
2. If yes: is the tool free/open-source, paid/SaaS, or unclear?
3. Tool name (if detected).

Respond as JSON only:
{"new_tool": true/false, "type": "free|paid|unclear", "tool_name": "..."}

Article title: {title}
Article summary: {summary}
"""


def detect_tool(article: dict, model: str, provider: str = "nvidia") -> dict:
    """Run tool detection LLM pass on a single article."""
    try:
        prompt = DETECT_PROMPT.format(
            title=article.get("title", ""),
            summary=article.get("summary", "")[:500],
        )
        result = generate_json(provider, model, prompt)
        return {**article, "detection": result}
    except Exception as e:
        return {**article, "detection": {"new_tool": False, "error": str(e)}}
