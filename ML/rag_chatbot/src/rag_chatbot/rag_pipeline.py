"""RAG pipeline composition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import RagSettings
from .documents import Document, DocumentChunk, chunk_document, load_documents
from .embeddings import HuggingFaceInferenceEmbedder
from .internet import InternetResearcher, WebDocument
from .llm_openrouter import OpenRouterClient
from .vector_store import InMemoryVectorStore, SearchHit


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[dict[str, str | float]]


class RagChatbot:
    def __init__(
        self,
        settings: RagSettings,
        *,
        embedder: HuggingFaceInferenceEmbedder | None = None,
        llm: OpenRouterClient | None = None,
        vector_store: InMemoryVectorStore | None = None,
        internet: InternetResearcher | None = None,
    ) -> None:
        self.settings = settings
        self.embedder = embedder or HuggingFaceInferenceEmbedder(settings)
        self.llm = llm or OpenRouterClient(settings)
        self.vector_store = vector_store or InMemoryVectorStore()
        self.internet = internet or InternetResearcher()

    async def index_paths(self, paths: list[str | Path]) -> int:
        documents = load_documents(paths)
        chunks = self._chunk_documents(documents)
        if not chunks:
            return 0
        embeddings = await self.embedder.embed_documents([chunk.text for chunk in chunks])
        self.vector_store.add_many(chunks, embeddings)
        return len(chunks)

    def _chunk_documents(self, documents: list[Document]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for document in documents:
            chunks.extend(
                chunk_document(
                    document,
                    chunk_size=self.settings.chunk_size,
                    overlap=self.settings.chunk_overlap,
                )
            )
        return chunks

    async def _retrieve_local(self, question: str, *, top_k: int) -> list[SearchHit]:
        if len(self.vector_store) == 0:
            return []
        query_embedding = await self.embedder.embed_query(question)
        return self.vector_store.search(query_embedding, top_k=top_k)

    async def _retrieve_web(self, question: str, *, top_k: int) -> list[SearchHit]:
        web_docs = await self.internet.search_and_fetch(question, max_results=self.settings.web_results)
        documents = [
            Document(
                id=document.url,
                text=document.text,
                metadata={"source": document.url, "title": document.title, "kind": "web"},
            )
            for document in web_docs
        ]
        chunks = self._chunk_documents(documents)
        if not chunks:
            return []
        embeddings = await self.embedder.embed_documents([chunk.text for chunk in chunks])
        temp_store = InMemoryVectorStore()
        temp_store.add_many(chunks, embeddings)
        query_embedding = await self.embedder.embed_query(question)
        return temp_store.search(query_embedding, top_k=top_k)

    async def answer(self, question: str, *, use_web: bool = False, top_k: int | None = None) -> RagAnswer:
        top_k = top_k or self.settings.top_k
        local_hits = await self._retrieve_local(question, top_k=top_k)
        web_hits = await self._retrieve_web(question, top_k=top_k) if use_web else []
        hits = sorted([*local_hits, *web_hits], key=lambda hit: hit.score, reverse=True)[:top_k]

        context = self._format_context(hits)
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты RAG-ассистент проекта MMAS Service. Отвечай по-русски, "
                    "опирайся на контекст и не выдумывай факты, которых в нем нет."
                ),
            },
            {
                "role": "user",
                "content": f"Вопрос:\n{question}\n\nКонтекст:\n{context}",
            },
        ]
        answer = await self.llm.complete(messages)
        return RagAnswer(
            answer=answer,
            sources=[
                {
                    "source": hit.chunk.metadata.get("source", hit.chunk.id),
                    "kind": hit.chunk.metadata.get("kind", "unknown"),
                    "score": round(hit.score, 4),
                }
                for hit in hits
            ],
        )

    @staticmethod
    def _format_context(hits: list[SearchHit]) -> str:
        if not hits:
            return "Контекст не найден."
        blocks = []
        for index, hit in enumerate(hits, start=1):
            source = hit.chunk.metadata.get("source", hit.chunk.id)
            blocks.append(f"[{index}] source={source}\n{hit.chunk.text}")
        return "\n\n".join(blocks)
