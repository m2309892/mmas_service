from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.models.students.belt import Belt


async def list_belts(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Belt]:
    result = await db.execute(
        select(Belt).order_by(Belt.sort_order, Belt.code).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_belt_by_code(db: AsyncSession, code: str) -> Belt:
    result = await db.execute(select(Belt).where(Belt.code == code))
    belt = result.scalar_one_or_none()
    if belt is None:
        raise NotFoundError(f"Belt with code={code} not found")
    return belt


async def create_belt(
    db: AsyncSession,
    *,
    code: str,
    color: str,
    style: Optional[str] = None,
    sort_order: int = 0,
) -> Belt:
    normalized = code.strip().lower()
    existing = await db.execute(select(Belt).where(Belt.code == normalized))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Belt with code={normalized} already exists")

    belt = Belt(code=normalized, color=color, style=style, sort_order=sort_order)
    db.add(belt)
    await db.commit()
    await db.refresh(belt)
    return belt


async def update_belt(
    db: AsyncSession,
    *,
    code: str,
    color: Optional[str] = None,
    style: Optional[str] = None,
    sort_order: Optional[int] = None,
) -> Belt:
    belt = await get_belt_by_code(db, code)
    if color is not None:
        belt.color = color
    if style is not None:
        belt.style = style
    if sort_order is not None:
        belt.sort_order = sort_order
    await db.commit()
    await db.refresh(belt)
    return belt


async def delete_belt(db: AsyncSession, *, code: str) -> None:
    from app.models.students.student import Student

    belt = await get_belt_by_code(db, code)
    linked = await db.execute(
        select(Student.id).where(Student.belt_id == belt.id).limit(1)
    )
    if linked.scalar_one_or_none() is not None:
        raise ConflictError(f"Cannot delete belt {code}: students are linked")
    await db.delete(belt)
    await db.commit()
