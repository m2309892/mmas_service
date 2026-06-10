# model_ottok

Черновая инфраструктура модели оттока клиентов MMAS.

Модуль намеренно сделан без обязательных ML-зависимостей: синтетика, обучение и инференс работают на стандартной библиотеке Python. Это удобно для первого прототипа и CI. Позже `logistic_model.py` можно заменить на sklearn/CatBoost, сохранив `features.py`, формат датасета и prediction log.

## Что внутри

- `src/model_ottok/features.py` - единый список признаков и валидация строки.
- `src/model_ottok/synthetic_data.py` - генератор синтетических клиентов, похожих на домен проекта: посещаемость, баланс, абонементы, задолженность, пояс, возраст.
- `src/model_ottok/logistic_model.py` - простая логистическая регрессия с нормализацией и сохранением в JSON.
- `src/model_ottok/train.py` - CLI для генерации синтетики и обучения.
- `src/model_ottok/predict.py` - CLI для локального инференса по JSON.
- `src/model_ottok/real_data_logging.py` - набросок безопасного логгирования реальных feature snapshots и prediction logs в JSONL.
- `sql/feature_snapshot_draft.sql` - черновик таблиц для будущей PostgreSQL-интеграции.

## Быстрый запуск

Из папки `ML/model_ottok`:

```bash
PYTHONPATH=src python3 -m model_ottok.train \
  --rows 3000 \
  --dataset-out artifacts/synthetic_churn.csv \
  --model-out artifacts/churn_model.json
```

Проверить инференс:

```bash
PYTHONPATH=src python3 -m model_ottok.predict \
  --model artifacts/churn_model.json \
  --input examples/sample_features.json
```

## Идея target

Для синтетики `is_churned=1` означает высокий риск ухода в следующие 30-45 дней. В реальной схеме target лучше считать постфактум:

- snapshot date = дата расчета признаков;
- churn window = 45 дней после snapshot;
- churned = нет посещений и нет покупки/продления абонемента в churn window.

## Реальные данные: где логгировать

Черновые точки интеграции в текущем backend:

- после создания посещений в `app/services/attendance/service.py`;
- после покупки/выдачи абонемента в `app/services/billing/service.py`;
- при nightly/job расчете признаков по всем активным студентам;
- при каждом prediction request, если модель будет подключена к API.

Важно: не логгировать ФИО, телефон, Telegram ID и сырой `mmas_id`. В `real_data_logging.py` есть `hash_mmas_id`, чтобы писать только salted hash.
