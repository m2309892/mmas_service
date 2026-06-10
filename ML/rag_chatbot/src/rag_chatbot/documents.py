"""Local document loading and chunking."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    text: str
    metadata: dict[str, str]


def iter_text_paths(paths: Iterable[str | Path]) -> list[Path]:
    result: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            result.extend(
                sorted(
                    child
                    for child in path.rglob("*")
                    if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS
                )
            )
        elif path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            result.append(path)
    return result


def load_documents(paths: Iterable[str | Path]) -> list[Document]:
    documents: list[Document] = []
    for path in iter_text_paths(paths):
        text = path.read_text(encoding="utf-8", errors="ignore")
        documents.append(
            Document(
                id=str(path),
                text=text,
                metadata={"source": str(path), "kind": "local_file"},
            )
        )
    return documents


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    chunks: list[str] = []
    start = 0
    normalized = text.strip()
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = end - overlap
    return chunks


def chunk_document(document: Document, *, chunk_size: int, overlap: int) -> list[DocumentChunk]:
    chunks = []
    for index, text in enumerate(chunk_text(document.text, chunk_size=chunk_size, overlap=overlap)):
        chunks.append(
            DocumentChunk(
                id=f"{document.id}::chunk-{index}",
                text=text,
                metadata={**document.metadata, "chunk_index": str(index)},
            )
        )
    return chunks
