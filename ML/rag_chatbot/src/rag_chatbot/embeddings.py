"""Hugging Face Inference API embeddings."""

from __future__ import annotations

from typing import Any

from .config import RagSettings


def _is_number_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, (int, float)) for item in value)


def _mean_pool(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    width = len(vectors[0])
    return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(width)]


def _as_vector(value: Any) -> list[float]:
    if _is_number_list(value):
        return [float(item) for item in value]
    if isinstance(value, list) and value and all(_is_number_list(item) for item in value):
        return _mean_pool([[float(number) for number in item] for item in value])
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
        return _as_vector(value[0])
    raise ValueError("Unexpected embedding response shape from Hugging Face")


class HuggingFaceInferenceEmbedder:
    def __init__(self, settings: RagSettings, *, timeout: float = 60.0) -> None:
        self.settings = settings
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.hf_api_token:
            headers["Authorization"] = f"Bearer {self.settings.hf_api_token}"
        return headers

    def _format_passages(self, texts: list[str]) -> list[str]:
        if self.settings.hf_embedding_model.startswith("intfloat/multilingual-e5"):
            return [f"passage: {text}" for text in texts]
        return texts

    def _format_query(self, text: str) -> str:
        if self.settings.hf_embedding_model.startswith("intfloat/multilingual-e5"):
            return f"query: {text}"
        return text

    async def _embed_raw(self, texts: list[str]) -> list[list[float]]:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("Install ML/rag_chatbot/requirements.txt to call Hugging Face") from exc

        url = (
            f"{self.settings.hf_inference_base_url}/pipeline/feature-extraction/"
            f"{self.settings.hf_embedding_model}"
        )
        payload = {"inputs": texts, "options": {"wait_for_model": True}}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()

        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"Hugging Face inference error: {data['error']}")
        if len(texts) == 1:
            return [_as_vector(data)]
        if isinstance(data, list):
            return [_as_vector(item) for item in data]
        raise ValueError("Unexpected embedding response from Hugging Face")

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed_raw(self._format_passages(texts))

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed_raw([self._format_query(text)]))[0]
