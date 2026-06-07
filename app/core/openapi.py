from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": "Вход staff и студентов, обновление access/refresh JWT.",
    },
    {
        "name": "users",
        "description": "Управление staff-пользователями (admin, trainer). Только admin.",
    },
    {
        "name": "accounts",
        "description": "Привязка Telegram-аккаунтов к студентам (mmas_id).",
    },
    {
        "name": "studios",
        "description": "Студии сети. CRUD — admin; чтение — без авторизации.",
    },
    {
        "name": "belts",
        "description": "Справочник поясов. CRUD — admin; чтение — без авторизации.",
    },
    {
        "name": "students",
        "description": "Студенты, баланс и история операций. Мутации — staff с доступом к студии.",
    },
    {
        "name": "events",
        "description": "Типы занятий и цены по студиям.",
    },
    {
        "name": "attendance",
        "description": "Посещаемость, оплата долгов, статистика.",
    },
    {
        "name": "billing",
        "description": "Абонементы: выдача staff и покупка с баланса.",
    },
]

PUBLIC_OPERATIONS = {
    ("get", "/"),
    ("get", "/health"),
    ("post", "/api/auth/login/staff"),
    ("post", "/api/auth/login/student"),
    ("post", "/api/auth/refresh"),
    ("get", "/api/studios/"),
    ("get", "/api/studios/{short_name}"),
    ("get", "/api/belts/"),
    ("get", "/api/belts/{code}"),
    ("get", "/api/students/"),
    ("get", "/api/students/projection"),
    ("get", "/api/students/balance/by-tg/{tg_id}"),
    ("get", "/api/students/balance/{mmas_id}"),
    ("get", "/api/students/balance/history/{mmas_id}"),
    ("get", "/api/students/{mmas_id}"),
    ("get", "/api/events/"),
    ("get", "/api/events/{studio_short_name}/{code}"),
    ("get", "/api/attendance/unpaid/{mmas_id}"),
    ("get", "/api/attendance/by-date"),
    ("get", "/api/attendance/stats/by-date"),
    ("get", "/api/attendance/stats/student/{mmas_id}"),
    ("get", "/api/attendance/stats/studio/{studio_short_name}"),
    ("get", "/api/billing/aboniment/{mmas_id}"),
    ("get", "/api/billing/aboniment/{mmas_id}/{studio_short_name}"),
}


def setup_openapi(app: FastAPI) -> None:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=OPENAPI_TAGS,
        )
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Access token из /api/auth/login/staff или /api/auth/login/student",
            }
        }

        for path, path_item in schema["paths"].items():
            for method, operation in path_item.items():
                if method.startswith("x-"):
                    continue
                if (method, path) not in PUBLIC_OPERATIONS:
                    operation["security"] = [{"BearerAuth": []}]

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
