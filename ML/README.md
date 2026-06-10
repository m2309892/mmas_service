# ML workspace

Эта папка отделяет ML-эксперименты от основного FastAPI backend.

## Состав

- `model_ottok/` - базовая модель оттока клиентов на синтетических данных и черновой контракт логгирования реальных признаков.
- `rag_chatbot/` - инфраструктура RAG-чатбота: OpenRouter как LLM, Hugging Face Inference API как embedder, простой vector store и модуль интернет-поиска.

## Принципы

- Тяжелые артефакты, датасеты и обученные модели должны храниться в `artifacts/`, `data/` или внешнем хранилище и не попадать в git.
- Интеграция с основным API должна идти через явные контракты: feature snapshots, prediction logs, RAG API/CLI.
