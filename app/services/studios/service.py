from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.models.studios.studio import Studio


async def list_studios(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Studio]:
    result = await db.execute(
        select(Studio).order_by(Studio.short_name).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_studio_by_short_name(db: AsyncSession, short_name: str) -> Studio:
    normalized = short_name.strip().upper()
    result = await db.execute(
        select(Studio).where(Studio.short_name == normalized)
    )
    studio = result.scalar_one_or_none()
    if studio is None:
        raise NotFoundError(f"Studio with short_name={short_name} not found")
    return studio


async def create_studio(db: AsyncSession, *, name: str, short_name: str) -> Studio:
    normalized = short_name.strip().upper()
    existing = await db.execute(
        select(Studio).where(Studio.short_name == normalized)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Studio with short_name={normalized} already exists")

    now = datetime.now()
    studio = Studio(
        name=name,
        short_name=normalized,
        students_cnt=0,
        created_at=now,
        updated_at=now,
    )
    db.add(studio)
    await db.commit()
    await db.refresh(studio)
    return studio


async def update_studio(
    db: AsyncSession, *, short_name: str, name: Optional[str] = None
) -> Studio:
    studio = await get_studio_by_short_name(db, short_name)
    if name is not None:
        studio.name = name
    studio.updated_at = datetime.now()
    await db.commit()
    await db.refresh(studio)
    return studio


async def delete_studio(db: AsyncSession, *, short_name: str) -> None:
    studio = await get_studio_by_short_name(db, short_name)
    if studio.students_cnt > 0:
        raise ConflictError(
            f"Cannot delete studio {short_name}: {studio.students_cnt} students linked"
        )
    await db.delete(studio)
    await db.commit()


async def recalc_students_cnt(db: AsyncSession, studio_id: int) -> None:
    from app.models.students.student import Student

    result = await db.execute(
        select(func.count()).select_from(Student).where(Student.studio_id == studio_id)
    )
    count = result.scalar_one()
    studio_result = await db.execute(select(Studio).where(Studio.id == studio_id))
    studio = studio_result.scalar_one()
    studio.students_cnt = count
    studio.updated_at = datetime.now()
