"""
llm_provider.py (v5.52.0 — Wave 64)

LLMProvider — pluggable LLM backend with Nova stub.

Interface:
  class LLMProvider(ABC):
    def complete(prompt, max_tokens, temperature) -> LLMResponse
    def summarize(text, target_tokens) -> str
    def extract_entities(text) -> List[str]

Backends:
  NoOpProvider   — default in DEMO mode: returns deterministic canned responses
  NovaProvider   — stub for Amazon Nova or custom Nova endpoint
                   Activated only when:
                     LLM_PROVIDER=nova AND NOVA_API_KEY is non-empty
                     AND ALLOW_LLM_IN_DEMO=1 (if in DEMO mode)

Safety:
  - In DEMO mode, LLM calls are gated: only NoOpProvider (canned) unless
    ALLOW_LLM_IN_DEMO=1 (test override)
  - No real network calls in any test configuration
  - All NoOpProvider responses are deterministic (same input → same output)

Endpoints:
  POST /llm/complete          — complete a prompt
  POST /llm/summarize         — summarize text
  POST /llm/extract-entities  — extract entities from text
  GET  /llm/provider          — active provider info
  GET  /llm/health            — health check (always OK)
"""
from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"


# ── Data types ─────────────────────────────────────────────────────────────────


class LLMResponse:
    def __init__(
        self,
        text: str,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        deterministic: bool = True,
    ):
        self.text = text
        self.model = model
        self.provider = provider
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.deterministic = deterministic

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "deterministic": self.deterministic,
            "generated_at": ASOF,
        }


# ── Provider interface ─────────────────────────────────────────────────────────


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse: ...

    @abstractmethod
    def summarize(self, text: str, target_tokens: int = 100) -> str: ...

    @abstractmethod
    def extract_entities(self, text: str) -> List[str]: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...


# ── NoOpProvider (default/demo) ────────────────────────────────────────────────


_CANNED_COMPLETIONS = [
    "Risk analysis complete. No material exposures identified in the current portfolio.",
    "Scenario impact assessed. All positions within acceptable VaR thresholds.",
    "Compliance check passed. License terms satisfied for all ingested datasets.",
    "Decision packet reviewed and approved. Signing key verification successful.",
    "Deployment readiness confirmed. All critical checks passed.",
]


class NoOpProvider(LLMProvider):
    """
    Deterministic no-op provider.
    Returns canned responses based on prompt hash — same input → same output.
    No network calls, no API keys required.
    """

    @property
    def provider_name(self) -> str:
        return "noop"

    @property
    def model_name(self) -> str:
        return "noop-v1"

    def _pick(self, text: str) -> str:
        idx = int(hashlib.md5(text.encode()).hexdigest(), 16) % len(_CANNED_COMPLETIONS)
        return _CANNED_COMPLETIONS[idx]

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> LLMResponse:
        response_text = self._pick(prompt)
        return LLMResponse(
            text=response_text,
            model=self.model_name,
            provider=self.provider_name,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(response_text.split()),
            deterministic=True,
        )

    def summarize(self, text: str, target_tokens: int = 100) -> str:
        words = text.split()
        truncated = words[:target_tokens]
        return " ".join(truncated) + (" [...]" if len(words) > target_tokens else "")

    def extract_entities(self, text: str) -> List[str]:
        # Deterministic: extract capitalized words as entities
        words = text.split()
        entities = list({w.strip(".,;:") for w in words if w and w[0].isupper()})
        entities.sort()
        return entities


# ── NovaProvider stub ──────────────────────────────────────────────────────────


class NovaProvider(LLMProvider):
    """
    Amazon Nova / custom Nova API stub.
    Activated only with LLM_PROVIDER=nova + NOVA_API_KEY set.
    In DEMO mode: requires ALLOW_LLM_IN_DEMO=1 to proceed.
    In stub mode: delegates to NoOpProvider, never makes network calls.
    """

    def __init__(self, api_key: str, endpoint: str = "", model: str = "nova-lite-v1") -> None:
        self._api_key = api_key
        self._endpoint = endpoint or "https://nova-api.example.com"
        self._model = model
        self._noop = NoOpProvider()  # stub fallback

    @property
    def provider_name(self) -> str:
        return "nova"

    @property
    def model_name(self) -> str:
        return self._model

    def complete(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> LLMResponse:
        # Stub: always delegate to noop — no real API calls
        resp = self._noop.complete(prompt, max_tokens, temperature)
        return LLMResponse(
            text=resp.text,
            model=self.model_name,
            provider=self.provider_name,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
            deterministic=True,
        )

    def summarize(self, text: str, target_tokens: int = 100) -> str:
        return self._noop.summarize(text, target_tokens)

    def extract_entities(self, text: str) -> List[str]:
        return self._noop.extract_entities(text)


# ── Provider selection ─────────────────────────────────────────────────────────


class LLMGateError(RuntimeError):
    """Raised when LLM is requested in demo mode without ALLOW_LLM_IN_DEMO=1."""
    pass


def _create_provider() -> LLMProvider:
    llm_backend = os.getenv("LLM_PROVIDER", "noop")
    nova_key = os.getenv("NOVA_API_KEY", "")
    allow_demo = os.getenv("ALLOW_LLM_IN_DEMO", "0") == "1"

    if llm_backend == "nova" and nova_key:
        if DEMO_MODE and not allow_demo:
            # Gate: refuse activation in demo mode unless explicitly allowed
            return NoOpProvider()
        return NovaProvider(
            api_key=nova_key,
            endpoint=os.getenv("NOVA_ENDPOINT", ""),
            model=os.getenv("NOVA_MODEL", "nova-lite-v1"),
        )

    return NoOpProvider()


_provider: LLMProvider = _create_provider()


def get_provider() -> LLMProvider:
    return _provider


# ── HTTP Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/llm", tags=["llm-provider"])


class CompleteRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.0


class SummarizeRequest(BaseModel):
    text: str
    target_tokens: int = 100


class ExtractEntitiesRequest(BaseModel):
    text: str


@router.post("/complete")
def http_complete(req: CompleteRequest):
    resp = get_provider().complete(req.prompt, req.max_tokens, req.temperature)
    return resp.to_dict()


@router.post("/summarize")
def http_summarize(req: SummarizeRequest):
    summary = get_provider().summarize(req.text, req.target_tokens)
    return {
        "summary": summary,
        "provider": get_provider().provider_name,
        "model": get_provider().model_name,
    }


@router.post("/extract-entities")
def http_extract_entities(req: ExtractEntitiesRequest):
    entities = get_provider().extract_entities(req.text)
    return {
        "entities": entities,
        "count": len(entities),
        "provider": get_provider().provider_name,
    }


@router.get("/provider")
def http_provider():
    return {
        "provider": get_provider().provider_name,
        "model": get_provider().model_name,
        "demo_mode": DEMO_MODE,
        "deterministic": True,
    }


@router.get("/health")
def http_health():
    return {"status": "ok", "provider": get_provider().provider_name, "asof": ASOF}
