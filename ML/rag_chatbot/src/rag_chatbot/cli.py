"""CLI entry point for the RAG prototype."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .config import RagSettings
from .rag_pipeline import RagChatbot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask the MMAS RAG chatbot")
    parser.add_argument("--docs", action="append", default=[], help="File or directory to index")
    parser.add_argument("--question", required=True)
    parser.add_argument("--web", action="store_true", help="Enable internet search enrichment")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    settings = RagSettings.from_env(args.env_file)
    chatbot = RagChatbot(settings)

    indexed_chunks = 0
    if args.docs:
        indexed_chunks = await chatbot.index_paths(args.docs)

    result = await chatbot.answer(args.question, use_web=args.web, top_k=args.top_k)
    print(result.answer)
    print()
    print(
        json.dumps(
            {
                "indexed_chunks": indexed_chunks,
                "sources": result.sources,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
