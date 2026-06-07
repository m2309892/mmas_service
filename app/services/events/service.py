from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ConflictError
from app.models.attendance.event import Event
from app.models.attendance.attendance import Attendance
from app.services.studios.service import get_studio_by_short_name


async def list_events(
    db: AsyncSession,
    *,
    studio_short_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Event]:
    stmt = select(Event).options(selectinload(Event.studio))
    if studio_short_name is not None:
        studio = await get_studio_by_short_name(db, studio_short_name)
        stmt = stmt.where(Event.studio_id == studio.id)
    stmt = stmt.order_by(Event.studio_id, Event.code).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_event_by_code(
    db: AsyncSession, *, studio_short_name: str, code: str
) -> Event:
    studio = await get_studio_by_short_name(db, studio_short_name)
    normalized = code.strip().lower()
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.studio))
        .where((Event.studio_id == studio.id) & (Event.code == normalized))
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise NotFoundError(
            f"Event code={code} not found in studio {studio_short_name}"
        )
    return event


async def get_default_event_for_studio(db: AsyncSession, studio_id: int) -> Event:
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.studio))
        .where(Event.studio_id == studio_id)
        .order_by(Event.price.asc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise NotFoundError(f"No events found for studio_id={studio_id}")
    return event


async def create_event(
    db: AsyncSession,
    *,
    studio_short_name: str,
    code: str,
    type: str,
    price: Decimal,
    description: Optional[str] = None,
) -> Event:
    studio = await get_studio_by_short_name(db, studio_short_name)
    normalized = code.strip().lower()

    existing = await db.execute(
        select(Event).where(
            (Event.studio_id == studio.id) & (Event.code == normalized)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            f"Event code={normalized} already exists in studio {studio.short_name}"
        )

    event = Event(
        code=normalized,
        type=type,
        price=price,
        description=description,
        studio_id=studio.id,
        created_at=datetime.now(),
    )
    db.add(event)
    await db.commit()
    return await get_event_by_code(db, studio_short_name=studio.short_name, code=normalized)


async def update_event(
    db: AsyncSession,
    *,
    studio_short_name: str,
    code: str,
    type: Optional[str] = None,
    price: Optional[Decimal] = None,
    description: Optional[str] = None,
) -> Event:
    event = await get_event_by_code(db, studio_short_name=studio_short_name, code=code)
    if type is not None:
        event.type = type
    if price is not None:
        event.price = price
    if description is not None:
        event.description = description
    await db.commit()
    return await get_event_by_code(db, studio_short_name=studio_short_name, code=code)


async def delete_event(db: AsyncSession, *, studio_short_name: str, code: str) -> None:
    event = await get_event_by_code(db, studio_short_name=studio_short_name, code=code)
    linked = await db.execute(
        select(Attendance.id).where(Attendance.event_id == event.id).limit(1)
    )
    if linked.scalar_one_or_none() is not None:
        raise ConflictError(f"Cannot delete event {code}: attendance records exist")
    await db.delete(event)
    await db.commit()
