"""Credential-safe discovery and inference adapters for supported model providers."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx


PROVIDERS = {
    "nvidia": {"env": "NVIDIA_API_KEY", "base": "https://integrate.api.nvidia.com/v1", "models": "/models"},
    "openrouter": {"env": "OPENROUTER_API_KEY", "base": "https://openrouter.ai/api/v1", "models": "/models?output_modalities=all"},
    "gemini": {"env": "GEMINI_API_KEY", "base": "https://generativelanguage.googleapis.com/v1beta", "models": "/models"},
    "featherless": {"env": "FEATHERLESS_API_KEY", "base": "https://api.featherless.ai/v1", "models": "/models?available_on_current_plan=true&per_page=1000"},
    "openai": {"env": "OPENAI_API_KEY", "base": "https://api.openai.com/v1", "models": "/models"},
}

LOCAL_ENDPOINTS = {
    "lm-studio": "http://127.0.0.1:1234/v1/models",
    "vllm": "http://127.0.0.1:8000/v1/models",
    "llama-cpp": "http://127.0.0.1:8080/v1/models",
    "ollama-local": "http://127.0.0.1:11434/api/tags",
}


def credential_statuses() -> dict[str, str]:
    """Return provider presence only; secret material never leaves the process."""
    return {provider: "configured" if os.getenv(spec["env"]) else "missing" for provider, spec in PROVIDERS.items()}


def credential_status(provider: str = "nvidia") -> str:
    """Return one provider's presence state."""
    return credential_statuses().get(provider, "unsupported")


def save_user_credential(provider: str, value: str) -> str:
    """Persist one credential to the current Windows user's environment."""
    if provider not in PROVIDERS:
        raise ValueError("Unsupported provider")
    value = value.strip()
    if len(value) < 12 or any(character.isspace() for character in value):
        raise ValueError("The API key format is invalid")
    env_name = PROVIDERS[provider]["env"]
    if os.name != "nt":
        raise RuntimeError("In-app credential persistence is supported on Windows only")
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, env_name, 0, winreg.REG_SZ, value)
    os.environ[env_name] = value
    return env_name


def _remote_headers(provider: str) -> dict[str, str]:
    key = os.getenv(PROVIDERS[provider]["env"])
    if not key:
        raise RuntimeError(f"{PROVIDERS[provider]['env']} is not configured")
    if provider == "gemini":
        return {"x-goog-api-key": key}
    return {"Authorization": f"Bearer {key}"}


def _normalize_models(provider: str, payload: dict[str, Any]) -> list[dict]:
    if provider == "gemini":
        rows = payload.get("models", [])
        return [
            {"id": row.get("name", "").removeprefix("models/"), "name": row.get("displayName") or row.get("name"), "provider": provider, "metadata": {"methods": row.get("supportedGenerationMethods", [])}}
            for row in rows if row.get("name")
        ]
    rows = payload.get("data", [])
    return [
        {"id": row.get("id", ""), "name": row.get("name") or row.get("id", ""), "provider": provider, "metadata": {"context_length": row.get("context_length"), "pricing": row.get("pricing"), "available_on_current_plan": row.get("available_on_current_plan")}}
        for row in rows if row.get("id")
    ]


def discover_models(provider: str = "nvidia") -> list[dict]:
    """Return every model visible to one configured remote provider."""
    if provider not in PROVIDERS:
        raise ValueError("Unsupported provider")
    spec = PROVIDERS[provider]
    if provider == "featherless":
        models: list[dict] = []
        for page in range(1, 51):
            response = httpx.get(
                f"{spec['base']}{spec['models']}&page={page}",
                headers=_remote_headers(provider),
                timeout=30,
            )
            response.raise_for_status()
            batch = _normalize_models(provider, response.json())
            models.extend(batch)
            if len(batch) < 1000:
                break
        return models
    response = httpx.get(f"{spec['base']}{spec['models']}", headers=_remote_headers(provider), timeout=30)
    response.raise_for_status()
    return _normalize_models(provider, response.json())


def discover_local_models() -> list[dict]:
    """Probe common localhost model servers without starting or changing them."""
    models: list[dict] = []
    for provider, url in LOCAL_ENDPOINTS.items():
        try:
            response = httpx.get(url, timeout=0.8)
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("models", []) if provider == "ollama-local" else payload.get("data", [])
            for row in rows:
                model_id = row.get("name") if provider == "ollama-local" else row.get("id")
                if model_id:
                    models.append({"id": model_id, "name": model_id, "provider": provider, "metadata": {"local": True}})
        except (httpx.HTTPError, ValueError):
            continue
    return models


def test_model(model: str, provider: str = "nvidia") -> dict:
    """Run a minimal sanitized completion and return operational metadata."""
    started = time.perf_counter()
    result = generate_json(provider, model, 'Reply with this JSON only: {"status":"ok"}', max_tokens=16)
    return {"model": model, "provider": provider, "latency_ms": round((time.perf_counter() - started) * 1000), "result": result}


def generate_json(provider: str, model: str, prompt: str, max_tokens: int = 2048) -> dict:
    """Generate one JSON object through a configured OpenAI-compatible provider."""
    if provider == "gemini":
        key = os.getenv(PROVIDERS[provider]["env"])
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        response = httpx.post(
            f"{PROVIDERS[provider]['base']}/models/{model}:generateContent",
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"}}, timeout=90,
        )
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        if provider in PROVIDERS:
            base = PROVIDERS[provider]["base"]
            headers = {**_remote_headers(provider), "Content-Type": "application/json"}
        elif provider in LOCAL_ENDPOINTS:
            base = "http://127.0.0.1:11434/v1" if provider == "ollama-local" else LOCAL_ENDPOINTS[provider].rsplit("/models", 1)[0]
            headers = {"Content-Type": "application/json"}
        else:
            raise ValueError("Unsupported provider")
        response = httpx.post(
            f"{base}/chat/completions", headers=headers,
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0.2}, timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(content)
