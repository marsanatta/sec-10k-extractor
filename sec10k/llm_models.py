"""Escalation-tier model identifiers, kept SDK-free so the API and escalation layers can
reference the default and a fallback list without importing the optional Copilot SDK.

The live model list is the source of truth (queried via `copilot_client.list_models_sync` and
served by `GET /api/models`); `FALLBACK_MODELS` only keeps the picker populated and request
validation working when no token is configured (the $0/offline path)."""
from __future__ import annotations

DEFAULT_MODEL = "claude-opus-4.8"

FALLBACK_MODELS: list[dict[str, str]] = [
    {"id": "claude-opus-4.8", "name": "Claude Opus 4.8"},
    {"id": "claude-opus-4.7", "name": "Claude Opus 4.7"},
    {"id": "claude-opus-4.6", "name": "Claude Opus 4.6"},
    {"id": "claude-opus-4.5", "name": "Claude Opus 4.5"},
    {"id": "claude-sonnet-4.6", "name": "Claude Sonnet 4.6"},
    {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5"},
    {"id": "claude-haiku-4.5", "name": "Claude Haiku 4.5"},
    {"id": "gpt-5.5", "name": "GPT-5.5"},
    {"id": "gpt-5.4", "name": "GPT-5.4"},
    {"id": "gpt-5.4-mini", "name": "GPT-5.4 mini"},
    {"id": "gpt-5.3-codex", "name": "GPT-5.3-Codex"},
    {"id": "gpt-5-mini", "name": "GPT-5 mini"},
    {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro"},
    {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash"},
    {"id": "auto", "name": "Auto"},
]
