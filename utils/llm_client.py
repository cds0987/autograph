"""Thin wrapper around optional LLM providers."""

from __future__ import annotations

from typing import Any

import structlog

from ..core.config import GraphConfig
from ..core.exceptions import ConfigurationError, IntegrationUnavailableError

_log = structlog.get_logger(component="LLMClient")


class LLMClient:
    """Optional provider client used when the caller explicitly enables LLM mode."""

    def __init__(self, config: GraphConfig) -> None:
        self.config = config

    def is_enabled(self) -> bool:
        return bool(self.config.use_llm and self.config.llm_api_key)

    def complete_json(self, prompt: str) -> dict[str, Any]:
        if not self.is_enabled():
            raise ConfigurationError(
                "LLM mode is disabled. Set use_llm=True and provide llm_api_key."
            )
        provider = self.config.llm_provider.lower()
        if provider == "openai":
            return self._complete_with_openai(prompt)
        if provider == "anthropic":
            return self._complete_with_anthropic(prompt)
        raise ConfigurationError(f"Unsupported llm_provider: {self.config.llm_provider}")

    def _complete_with_openai(self, prompt: str) -> dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise IntegrationUnavailableError(
                "The openai package is not installed."
            ) from exc

        model = self.config.llm_model or "gpt-4.1-mini"
        _log.info("llm.request", provider="openai", model=model, prompt_chars=len(prompt))
        client = OpenAI(api_key=self.config.llm_api_key)
        response = client.responses.create(model=model, input=prompt)
        text = getattr(response, "output_text", "").strip()
        _log.info("llm.response", provider="openai", model=model, response_chars=len(text))
        return {"raw_text": text}

    def _complete_with_anthropic(self, prompt: str) -> dict[str, Any]:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise IntegrationUnavailableError(
                "The anthropic package is not installed."
            ) from exc

        client = Anthropic(api_key=self.config.llm_api_key)
        response = client.messages.create(
            model=self.config.llm_model or "claude-3-5-sonnet-latest",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        blocks = getattr(response, "content", [])
        text = "".join(getattr(block, "text", "") for block in blocks).strip()
        return {"raw_text": text}
