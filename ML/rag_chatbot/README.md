# rag_chatbot

Черновая инфраструктура RAG-чатбота для MMAS.

Здесь нет скачивания моделей. LLM вызывается через OpenRouter API, embedder вызывается через Hugging Face Inference API, а vector store пока in-memory. Этого достаточно, чтобы проверить архитектуру и позже заменить отдельные части на production-компоненты.

## Что внутри

- `config.py` - настройки из `.env`/переменных окружения.
- `llm_openrouter.py` - клиент OpenRouter Chat Completions.
- `embeddings.py` - embedder через Hugging Face Inference API.
- `documents.py` - загрузка локальных текстовых файлов и chunking.
- `vector_store.py` - простой cosine-search в памяти.
- `internet.py` - модуль похода в интернет: поиск через DuckDuckGo HTML и fetch страниц.
- `rag_pipeline.py` - сборка RAG-контекста и вызов LLM.
- `cli.py` - минимальная CLI-точка входа.

## Настройка

```bash
cp env.example .env
```

Заполнить:

- `OPENROUTER_API_KEY`
- `HF_API_TOKEN`, если выбранная HF Inference модель требует токен

Модели по умолчанию:

- LLM: `openai/gpt-4o-mini` через OpenRouter, можно заменить в `OPENROUTER_MODEL`;
- embeddings: `intfloat/multilingual-e5-small` через HF Inference API, можно заменить в `HF_EMBEDDING_MODEL`.

## Пример запуска

Из папки `ML/rag_chatbot`:

```bash
PYTHONPATH=src python3 -m rag_chatbot.cli \
  --docs ../../README.md \
  --question "Какие основные сущности есть в MMAS Service?"
```

С интернет-поиском:

```bash
PYTHONPATH=src python3 -m rag_chatbot.cli \
  --docs ../../README.md \
  --web \
  --question "Сравни текущую архитектуру проекта с типичным FastAPI backend"
```

## Production-направление

- заменить `InMemoryVectorStore` на pgvector/Qdrant/Weaviate;
- вынести ingestion в отдельный job;
- добавить allowlist доменов для web-fetch;
- логгировать question, retrieved source ids, latency, model name и token usage;
- добавить eval-набор вопросов по документации проекта.
