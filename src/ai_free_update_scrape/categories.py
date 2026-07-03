"""Editable category taxonomy and deterministic article classification."""

from __future__ import annotations

import json
import re
from pathlib import Path


CATEGORY_NAMES = [
    "Foundation model releases", "Reasoning models", "Multimodal models", "Image generation",
    "Video generation", "Speech and audio AI", "AI agents", "Agent frameworks",
    "MCP servers and integrations", "Developer SDKs and APIs", "Coding assistants",
    "Open-source repositories", "Local AI and edge inference", "Model optimization and quantization",
    "Training and fine-tuning", "Datasets and benchmarks", "Research papers",
    "AI infrastructure and GPUs", "Cloud AI services", "Product launches and feature updates",
    "Free tiers and promotions", "Open-source alternatives", "Pricing changes",
    "Funding, acquisitions, and company activity", "Regulation, policy, and safety",
    "Security vulnerabilities and incidents", "Tutorials and implementation guides",
    "Workflow automation", "Business use cases", "Creator tools and content production",
    "AI evaluation and observability", "Retrieval and AI search", "Robotics and embodied AI",
    "Healthcare and life sciences AI", "Finance and accounting AI", "Education AI",
    "Legal and compliance AI", "Privacy and responsible AI", "Synthetic data",
    "Customer support and conversational AI",
]

KEYWORDS = {
    "Foundation model releases": ["model release", "foundation model", "new model"],
    "Reasoning models": ["reasoning", "thinking model", "chain of thought"],
    "Multimodal models": ["multimodal", "vision language", "vlm"],
    "Image generation": ["image generation", "text-to-image", "diffusion"],
    "Video generation": ["video generation", "text-to-video", "video model"],
    "Speech and audio AI": ["speech", "audio", "voice", "text-to-speech"],
    "AI agents": ["ai agent", "agentic", "autonomous agent"],
    "Agent frameworks": ["agent framework", "multi-agent", "orchestration"],
    "MCP servers and integrations": ["mcp", "model context protocol"],
    "Developer SDKs and APIs": ["sdk", "api", "developer platform"],
    "Coding assistants": ["coding assistant", "code generation", "copilot"],
    "Open-source repositories": ["github", "repository", "open source"],
    "Local AI and edge inference": ["local ai", "on-device", "edge inference"],
    "Model optimization and quantization": ["quantization", "gguf", "optimization"],
    "Training and fine-tuning": ["fine-tuning", "training", "lora"],
    "Datasets and benchmarks": ["dataset", "benchmark", "leaderboard"],
    "Research papers": ["paper", "arxiv", "research"],
    "AI infrastructure and GPUs": ["gpu", "inference server", "accelerator"],
    "Cloud AI services": ["cloud ai", "managed ai", "vertex", "bedrock"],
    "Product launches and feature updates": ["launch", "feature", "update"],
    "Free tiers and promotions": ["free tier", "free plan", "promotion"],
    "Open-source alternatives": ["alternative", "self-hosted", "open-source"],
    "Pricing changes": ["pricing", "price change", "cost"],
    "Funding, acquisitions, and company activity": ["funding", "acquisition", "raises"],
    "Regulation, policy, and safety": ["regulation", "policy", "ai safety"],
    "Security vulnerabilities and incidents": ["vulnerability", "security incident", "cve"],
    "Tutorials and implementation guides": ["tutorial", "guide", "how to"],
    "Workflow automation": ["automation", "workflow", "no-code"],
    "Business use cases": ["business", "enterprise", "case study"],
    "Creator tools and content production": ["creator", "content production", "video editor"],
    "AI evaluation and observability": ["evaluation", "evals", "observability", "tracing"],
    "Retrieval and AI search": ["retrieval", "rag", "semantic search", "vector search"],
    "Robotics and embodied AI": ["robotics", "embodied ai", "humanoid"],
    "Healthcare and life sciences AI": ["healthcare ai", "medical ai", "drug discovery"],
    "Finance and accounting AI": ["finance ai", "accounting ai", "fintech ai"],
    "Education AI": ["education ai", "edtech", "ai tutor"],
    "Legal and compliance AI": ["legal ai", "compliance ai", "regtech"],
    "Privacy and responsible AI": ["privacy", "responsible ai", "ai governance"],
    "Synthetic data": ["synthetic data", "data generation"],
    "Customer support and conversational AI": ["customer support ai", "chatbot", "conversational ai"],
}


def default_categories() -> list[dict]:
    """Return safe editable defaults for the full category taxonomy."""
    return [
        {
            "id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
            "name": name,
            "enabled": True,
            "priority": index + 1,
            "include_keywords": KEYWORDS.get(name, []),
            "exclude_keywords": [],
            "source_ids": [],
            "result_target": 10,
            "mandatory_results": False,
            "freshness_hours": 72,
            "date_mode": "freshness",
            "date_start": "",
            "date_end": "",
            "minimum_relevance": 0.45,
            "color": ["#22d3ee", "#a78bfa", "#34d399", "#f59e0b", "#f472b6"][index % 5],
        }
        for index, name in enumerate(CATEGORY_NAMES)
    ]


def load_categories(path: Path) -> list[dict]:
    """Load persisted categories, creating the default taxonomy when absent."""
    if not path.exists():
        path.write_text(json.dumps(default_categories(), indent=2) + "\n", encoding="utf-8")
    saved = json.loads(path.read_text(encoding="utf-8"))
    saved_by_id = {item.get("id"): item for item in saved}
    return [{**item, **saved_by_id.get(item["id"], {})} for item in default_categories()]


def save_categories(path: Path, categories: list[dict]) -> None:
    """Persist validated category records."""
    path.write_text(json.dumps(categories, indent=2) + "\n", encoding="utf-8")


def classify_article(article: dict, categories: list[dict]) -> list[str]:
    """Return matching enabled category identifiers using configured keywords."""
    text = " ".join(str(article.get(key, "")) for key in ("title", "summary", "source")).lower()
    matches = []
    for category in categories:
        if not category.get("enabled", True):
            continue
        include = [word.lower() for word in category.get("include_keywords", []) if word]
        exclude = [word.lower() for word in category.get("exclude_keywords", []) if word]
        if include and any(word in text for word in include) and not any(word in text for word in exclude):
            matches.append(category["id"])
    return matches
