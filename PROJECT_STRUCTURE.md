# Структура проекта MMAS Service

Backend-only REST API (без Telegram-бота).

```
mmas_service/
├── alembic/                 # Миграции БД
├── app/
│   ├── api/                 # FastAPI роутеры
│   ├── core/                # config, db, jwt, deps, logging
│   ├── models/              # SQLAlchemy ORM
│   ├── repositories/        # Базовый CRUD (опционально)
│   ├── schemas/             # Pydantic
│   ├── services/            # Бизнес-логика
│   └── main.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── run_api.py
└── requirements.txt
```

## API модули

| Файл | Назначение |
|------|------------|
| `auth.py` | JWT login staff/student, refresh |
| `users.py` | CRUD staff (admin) |
| `accounts.py` | Привязка Telegram ↔ mmas_id |
| `studios.py`, `belts.py` | Справочники |
| `students.py` | Студенты, баланс |
| `events.py` | Занятия |
| `attendance.py` | Посещаемость, статистика |
| `billing.py` | Абонементы |

## Запуск

- Локально: `python run_api.py`
- Docker: `docker compose up -d`
