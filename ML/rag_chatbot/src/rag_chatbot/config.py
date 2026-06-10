"""Configuration helpers for the RAG chatbot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file(path: str | Path | None) -> None:
    if path is None:
        return
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


@dataclass(frozen=True)
class RagSettings:
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str = "http://localhost"
    openrouter_app_title: str = "MMAS RAG Chatbot"

    hf_api_token: str = ""
    hf_embedding_model: str = "intfloat/multilingual-e5-small"
    hf_inference_base_url: str = "https://api-inference.huggingface.co"

    chunk_size: int = 1200
    chunk_overlap: int = 180
    top_k: int = 5
    web_results: int = 3

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> "RagSettings":
        _load_env_file(env_file)
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_model=os.getenv("OPENROUTER_MODEL", cls.openrouter_model),
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", cls.openrouter_base_url).rstrip("/"),
            openrouter_http_referer=os.getenv("OPENROUTER_HTTP_REFERER", cls.openrouter_http_referer),
            openrouter_app_title=os.getenv("OPENROUTER_APP_TITLE", cls.openrouter_app_title),
            hf_api_token=os.getenv("HF_API_TOKEN", ""),
            hf_embedding_model=os.getenv("HF_EMBEDDING_MODEL", cls.hf_embedding_model),
            hf_inference_base_url=os.getenv("HF_INFERENCE_BASE_URL", cls.hf_inference_base_url).rstrip("/"),
            chunk_size=_get_int("RAG_CHUNK_SIZE", cls.chunk_size),
            chunk_overlap=_get_int("RAG_CHUNK_OVERLAP", cls.chunk_overlap),
            top_k=_get_int("RAG_TOP_K", cls.top_k),
            web_results=_get_int("RAG_WEB_RESULTS", cls.web_results),
        )

    def require_openrouter_key(self) -> None:
        if not self.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for LLM calls")
