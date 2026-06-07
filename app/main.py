from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import close_db, async_session
from app.core.exceptions import AppError
from app.core.logging import setup_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.openapi import OPENAPI_TAGS, setup_openapi
from app.api import auth, users, accounts, students, attendance, billing, studios, belts, events
from app.services.staff.service import bootstrap_admin_if_needed

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.debug, json_logs=settings.log_json)
    logger.info("app_starting", app_name=settings.app_name)
    async with async_session() as session:
        await bootstrap_admin_if_needed(session)
    yield
    await close_db()
    logger.info("app_stopped")


app = FastAPI(
    title=settings.app_name,
    description=(
        "REST API для сети студий боевых искусств: студенты, баланс, абонементы, "
        "посещаемость, staff-авторизация, привязка Telegram.\n\n"
        "**Роли:** `admin` — полный доступ; `trainer` — свои студии; `student` — только чтение.\n\n"
        "Защищённые методы требуют заголовок `Authorization: Bearer <access_token>`."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)

setup_openapi(app)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning(
        "app_error",
        detail=exc.detail,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(studios.router, prefix="/api/studios", tags=["studios"])
app.include_router(belts.router, prefix="/api/belts", tags=["belts"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])


@app.get(
    "/",
    summary="Информация об API",
    description="Версия сервиса и ссылка на Swagger UI.",
)
async def root():
    return {"message": "MMAS Service API", "version": "1.0.0", "docs": "/docs"}


@app.get(
    "/health",
    summary="Проверка доступности",
    description="Используется для health-check балансировщика и мониторинга.",
)
async def health_check():
    return {"status": "healthy"}
