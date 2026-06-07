from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.core.jwt import create_access_token, create_refresh_token, safe_decode_token
from app.core.security import verify_password
from app.models.accounts.staff_user import StaffUser, StaffRole
from app.models.students.student import Student
from app.schemas.auth import TokenResponse


def _token_response(
    *,
    subject: str,
    token_type: str,
    role: str,
    studios: list[str],
) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            subject=subject,
            token_type=token_type,
            role=role,
            studios=studios,
        ),
        refresh_token=create_refresh_token(
            subject=subject,
            token_type=token_type,
            role=role,
            studios=studios,
        ),
        role=role,
        studio_short_names=studios,
    )


async def login_staff(
    db: AsyncSession, *, username: str, password: str
) -> TokenResponse:
    result = await db.execute(
        select(StaffUser)
        .options(selectinload(StaffUser.studios))
        .where(StaffUser.username == username)
    )
    staff = result.scalar_one_or_none()
    if staff is None or not staff.is_active:
        raise AppError("Invalid username or password", status_code=401)
    if not verify_password(password, staff.hashed_password):
        raise AppError("Invalid username or password", status_code=401)

    studios = [s.short_name for s in staff.studios]
    return _token_response(
        subject=staff.username,
        token_type="staff",
        role=staff.role.value,
        studios=studios,
    )


async def login_student(
    db: AsyncSession, *, mmas_id: str, password: str
) -> TokenResponse:
    result = await db.execute(select(Student).where(Student.mmas_id == mmas_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise AppError("Invalid mmas_id or password", status_code=401)
    if not verify_password(password, student.hashed_password):
        raise AppError("Invalid mmas_id or password", status_code=401)

    return _token_response(
        subject=student.mmas_id,
        token_type="student",
        role="student",
        studios=[],
    )


async def refresh_tokens(db: AsyncSession, *, refresh_token: str) -> TokenResponse:
    payload = safe_decode_token(refresh_token)
    if payload is None or payload.get("token_kind") != "refresh":
        raise AppError("Invalid refresh token", status_code=401)

    subject = payload["sub"]
    token_type = payload["type"]
    role = payload["role"]
    studios = [s.upper() for s in payload.get("studios", [])]

    if token_type == "staff":
        result = await db.execute(
            select(StaffUser)
            .options(selectinload(StaffUser.studios))
            .where(StaffUser.username == subject)
        )
        staff = result.scalar_one_or_none()
        if staff is None or not staff.is_active:
            raise AppError("Invalid refresh token", status_code=401)
        studios = [s.short_name for s in staff.studios]
    else:
        result = await db.execute(select(Student).where(Student.mmas_id == subject))
        if result.scalar_one_or_none() is None:
            raise AppError("Invalid refresh token", status_code=401)

    return _token_response(
        subject=subject,
        token_type=token_type,
        role=role,
        studios=studios,
    )
