from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError, ConflictError
from app.core.security import hash_password
from app.models.accounts.staff_user import StaffUser, StaffRole
from app.models.studios.studio import Studio
from app.services.studios.service import get_studio_by_short_name


async def list_staff_users(
    db: AsyncSession, *, skip: int = 0, limit: int = 100
) -> List[StaffUser]:
    result = await db.execute(
        select(StaffUser)
        .options(selectinload(StaffUser.studios))
        .order_by(StaffUser.username)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_staff_by_username(db: AsyncSession, username: str) -> StaffUser:
    result = await db.execute(
        select(StaffUser)
        .options(selectinload(StaffUser.studios))
        .where(StaffUser.username == username)
    )
    staff = result.scalar_one_or_none()
    if staff is None:
        raise NotFoundError(f"Staff user {username} not found")
    return staff


async def _resolve_studios(
    db: AsyncSession, studio_short_names: list[str]
) -> List[Studio]:
    studios: List[Studio] = []
    for short_name in studio_short_names:
        studios.append(await get_studio_by_short_name(db, short_name))
    return studios


async def create_staff_user(
    db: AsyncSession,
    *,
    username: str,
    password: str,
    name: str,
    role: StaffRole,
    studio_short_names: Optional[list[str]] = None,
) -> StaffUser:
    existing = await db.execute(
        select(StaffUser).where(StaffUser.username == username)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Staff user {username} already exists")

    names = studio_short_names or []
    if role == StaffRole.TRAINER and not names:
        raise AppError("Trainer must be assigned to at least one studio")
    if role == StaffRole.ADMIN:
        names = []

    staff = StaffUser(
        username=username,
        hashed_password=hash_password(password),
        name=name,
        role=role,
        is_active=True,
        created_at=datetime.now(),
    )
    if names:
        staff.studios = await _resolve_studios(db, names)

    db.add(staff)
    await db.commit()
    return await get_staff_by_username(db, username)


async def update_staff_user(
    db: AsyncSession,
    *,
    username: str,
    name: Optional[str] = None,
    password: Optional[str] = None,
    is_active: Optional[bool] = None,
    studio_short_names: Optional[list[str]] = None,
) -> StaffUser:
    staff = await get_staff_by_username(db, username)

    if name is not None:
        staff.name = name
    if password is not None:
        staff.hashed_password = hash_password(password)
    if is_active is not None:
        staff.is_active = is_active
    if studio_short_names is not None:
        if staff.role == StaffRole.TRAINER and not studio_short_names:
            raise AppError("Trainer must be assigned to at least one studio")
        if staff.role == StaffRole.ADMIN:
            staff.studios = []
        else:
            staff.studios = await _resolve_studios(db, studio_short_names)

    await db.commit()
    return await get_staff_by_username(db, username)


async def bootstrap_admin_if_needed(db: AsyncSession) -> None:
    if not settings.admin_bootstrap_username or not settings.admin_bootstrap_password:
        return

    result = await db.execute(select(func.count()).select_from(StaffUser))
    if result.scalar_one() > 0:
        return

    await create_staff_user(
        db,
        username=settings.admin_bootstrap_username,
        password=settings.admin_bootstrap_password,
        name="Bootstrap Admin",
        role=StaffRole.ADMIN,
        studio_short_names=[],
    )
