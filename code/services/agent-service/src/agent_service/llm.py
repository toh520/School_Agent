"""OpenAI-compatible model adapter with bounded retries and credential-safe failures."""

import asyncio
import json
import re
from collections.abc import Callable
from typing import Any

import httpx

from agent_service.config import Settings


class ModelUnavailable(RuntimeError):
    """Publicly safe signal for missing configuration, timeout, or provider failure."""


class OpenAICompatibleModel:
    """Call SiliconFlow through its documented OpenAI-compatible chat endpoint."""

    def __init__(
        self,
        settings: Settings,
        config_loader: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self._provider = settings.llm_provider.strip().lower()
        self.model_name = settings.llm_model
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = (
            settings.llm_api_key.get_secret_value() if settings.llm_api_key is not None else ""
        )
        self._timeout = settings.llm_timeout_seconds
        self._max_retries = settings.llm_max_retries
        self._config_loader = config_loader

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        """Request a complete JSON object without imposing an application output quota."""

        payload = await self._request(
            {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            }
        )
        try:
            content = str(payload["choices"][0]["message"]["content"]).strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)
            return json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exception:
            raise ModelUnavailable("MODEL_INVALID_RESPONSE") from exception

    async def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        """Return a bounded answer so policy checks run before any text reaches the client."""

        payload = await self._request(
            {
                "model": self.model_name,
                "messages": [{"role": "system", "content": system}, *messages],
                "temperature": 0.1,
                "max_tokens": 220,
            }
        )
        try:
            return str(payload["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exception:
            raise ModelUnavailable("MODEL_INVALID_RESPONSE") from exception

    async def _request(self, body: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise ModelUnavailable("MODEL_NOT_CONFIGURED")
        runtime = await asyncio.to_thread(self._config_loader) if self._config_loader else {}
        provider = str(runtime.get("provider", self._provider)).strip().lower()
        model_name = str(runtime.get("model", self.model_name)).strip() or self.model_name
        base_url = str(runtime.get("baseUrl", self._base_url)).strip().rstrip("/")
        if not base_url.startswith(("https://", "http://")):
            raise ModelUnavailable("MODEL_INVALID_CONFIG")
        try:
            timeout = min(180.0, max(5.0, float(runtime.get("timeoutSeconds", self._timeout))))
            max_retries = min(5, max(0, int(runtime.get("maxRetries", self._max_retries))))
        except (TypeError, ValueError) as exception:
            raise ModelUnavailable("MODEL_INVALID_CONFIG") from exception
        body = {**body, "model": model_name}
        # SiliconFlow enables the Qwen3 reasoning mode by default. That mode can
        # spend thousands of tokens before returning the small JSON object this
        # application needs, which makes the 45-second recommendation boundary
        # expire. Recommendation and classification calls need deterministic,
        # low-latency output, so explicitly use the provider's non-thinking mode.
        if provider == "siliconflow" and model_name.startswith(("Qwen/Qwen3-", "Qwen/Qwen3.5-")):
            body = {**body, "enable_thinking": False}
        if provider == "siliconflow" and model_name == "deepseek-ai/DeepSeek-V4-Flash":
            body = {**body, "enable_thinking": False}
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        url = f"{base_url}/chat/completions"
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers, json=body)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPError, ValueError) as exception:
                if attempt >= max_retries:
                    raise ModelUnavailable("MODEL_UNAVAILABLE") from exception
                await asyncio.sleep(0.2 * (attempt + 1))
        raise ModelUnavailable("MODEL_UNAVAILABLE")
