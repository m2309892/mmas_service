"""OpenRouter chat completions client."""

from __future__ import annotations

from .config import RagSettings


class OpenRouterClient:
    def __init__(self, settings: RagSettings, *, timeout: float = 60.0) -> None:
        self.settings = settings
        self.timeout = timeout

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 900,
    ) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("Install ML/rag_chatbot/requirements.txt to call OpenRouter") from exc

        self.settings.require_openrouter_key()
        url = f"{self.settings.openrouter_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_http_referer,
            "X-Title": self.settings.openrouter_app_title,
        }
        payload = {
            "model": self.settings.openrouter_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
