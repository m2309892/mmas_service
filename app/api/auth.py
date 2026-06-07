from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import (
    StaffLoginRequest,
    StudentLoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.auth.service import login_staff, login_student, refresh_tokens

router = APIRouter()


@router.post(
    "/login/staff",
    response_model=TokenResponse,
    summary="Вход staff",
    description="Авторизация admin или trainer по username/password. Возвращает access и refresh JWT.",
)
async def api_login_staff(body: StaffLoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_staff(db, username=body.username, password=body.password)


@router.post(
    "/login/student",
    response_model=TokenResponse,
    summary="Вход студента",
    description="Авторизация студента по mmas_id и паролю. Токен только для чтения.",
)
async def api_login_student(
    body: StudentLoginRequest, db: AsyncSession = Depends(get_db)
):
    return await login_student(db, mmas_id=body.mmas_id, password=body.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновить токены",
    description="Выдаёт новую пару access/refresh по действительному refresh_token.",
)
async def api_refresh_token(
    body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    return await refresh_tokens(db, refresh_token=body.refresh_token)
