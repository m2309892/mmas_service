# MMAS Service

REST API backend для сети студий боевых искусств: студенты, баланс, абонементы, посещаемость, staff-авторизация, привязка Telegram-аккаунтов через API.

> Telegram-бот **не входит** в этот репозиторий — только backend. Бот/клиенты ходят в API.

## Стек

- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy 2 (async) + PostgreSQL
- Alembic, JWT, structlog

## Быстрый старт (локально)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

cp env.example .env             # заполнить SECRET_KEY, DATABASE_URL
alembic upgrade head
python run_api.py
```

Swagger: http://localhost:8000/docs

## Docker

```bash
cp env.example .env
docker compose up -d db
docker compose --profile migrate run --rm migrate
docker compose up -d api
```

API: http://localhost:8000

## Архитектура

```
HTTP → API → Service → SQLAlchemy → PostgreSQL
         ↑
    JWT auth (staff / student)
```


| Слой                  | Папка      |
| ------------------------- | --------------- |
| API                       | `app/api/`      |
| Бизнес-логика | `app/services/` |
| ORM                       | `app/models/`   |
| Схемы                | `app/schemas/`  |
| Ядро                  | `app/core/`     |

## Идентификаторы


| Сущность | Публичный ключ в API | Внутренний`id` |
| ---------------- | ---------------------------------- | ------------------------ |
| Студия     | `short_name`                       | скрыт               |
| Пояс / Event | `code`                             | скрыт               |
| Студент   | `mmas_id`                          | скрыт               |

## Auth

```bash
# Staff login
POST /api/auth/login/staff
{"username": "admin", "password": "..."}

# Header для mutating-запросов
Authorization: Bearer <access_token>
```


| Роль    | Права                                                                                               |
| ----------- | -------------------------------------------------------------------------------------------------------- |
| **admin**   | всё, создание staff и студий                                                           |
| **trainer** | свои студии (может быть**несколько**), студенты, attendance, balance |
| **student** | только login, без mutating staff-операций                                               |

Первый admin: `ADMIN_BOOTSTRAP_USERNAME/PASSWORD` в `.env` (создаётся при старте, если staff пуст).

Студентов создаёт **только staff** — `POST /api/students/` с токеном.

## Основные эндпоинты


| Группа              | Примеры                                                               |
| ------------------------- | ---------------------------------------------------------------------------- |
| Auth                      | `/api/auth/login/staff`, `/api/auth/refresh`                                 |
| Staff                     | `/api/users/staff` (admin)                                                   |
| Студии / пояса | `/api/studios/`, `/api/belts/`                                               |
| Студенты          | `/api/students/`, `/api/students/balance/{mmas_id}/credit`                   |
| Events                    | `/api/events/{studio}/{code}`                                                |
| Attendance                | `/api/attendance/bulk`, `/api/attendance/pay-unpaid/{mmas_id}`               |
| Stats                     | `/api/attendance/stats/by-date`, `/api/attendance/stats/studio/{short_name}` |
| Billing                   | `/api/billing/aboniment/{mmas_id}/purchase`                                  |
| TG (API)                  | `/api/accounts/tg/link` — привязка tg_id ↔ mmas_id                 |

## Логирование

- structlog + `X-Request-ID` в каждом ответе
- `LOG_JSON=true` в `.env` для JSON-логов в production

## Тесты

```bash
pytest
```

CI: `.github/workflows/ci.yml` — pytest на push/PR.
