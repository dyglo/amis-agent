from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str | None
    usage: dict | None
    latency_ms: int


class LLMClient:
    def __init__(self, *, base_url: str, api_key: str, timeout_s: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s

    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float = 0.4,
    ) -> LLMResponse:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        start = time.time()
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.time() - start) * 1000)
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage")
        model_name = data.get("model")
        return LLMResponse(content=content, model=model_name, usage=usage, latency_ms=latency_ms)
