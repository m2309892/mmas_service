from typing import List, Literal, Optional
from datetime import datetime, date, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, InsufficientBalanceError
from app.models.attendance.attendance import Attendance, PaidBy
from app.models.attendance.event import Event
from app.models.students.student import Student
from app.models.studios.studio import Studio
from app.services.billing.aboniment_helpers import (
    try_cover_with_aboniment,
    calculate_attendance_price,
)
from app.services.billing.balance_service import debit
from app.services.students.service import get_student_by_mmas_id
from app.services.studios.service import get_studio_by_short_name
from app.services.events.service import get_event_by_code, get_default_event_for_studio

PayMethod = Literal["auto", "balance", "aboniment"]

_ATTENDANCE_LOAD = (
    selectinload(Attendance.student),
    selectinload(Attendance.studio),
    selectinload(Attendance.event),
)


def _duration_hours(hours: time) -> float:
    return hours.hour + hours.minute / 60.0 + hours.second / 3600.0


def _count_by_paid_by(records: List[Attendance]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for att in records:
        key = att.paid_by.value
        counts[key] = counts.get(key, 0) + 1
    return counts


async def _reload_attendances(db: AsyncSession, ids: List[int]) -> List[Attendance]:
    if not ids:
        return []
    result = await db.execute(
        select(Attendance)
        .options(*_ATTENDANCE_LOAD)
        .where(Attendance.id.in_(ids))
        .order_by(Attendance.train_date.asc())
    )
    return result.scalars().all()


async def _load_event(db: AsyncSession, event_id: int) -> Event:
    result = await db.execute(
        select(Event).options(selectinload(Event.studio)).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise NotFoundError(f"Event with id={event_id} not found")
    return event


async def _resolve_event(
    db: AsyncSession,
    *,
    studio_id: int,
    studio_short_name: str,
    event_code: Optional[str],
) -> Event:
    if event_code:
        return await get_event_by_code(
            db, studio_short_name=studio_short_name, code=event_code
        )
    return await get_default_event_for_studio(db, studio_id)


async def _charge_from_balance(
    db: AsyncSession, att: Attendance, event: Event
) -> bool:
    total = calculate_attendance_price(event, att)
    try:
        await debit(
            db,
            student_id=att.student_id,
            amount=total,
            comment=f"Оплата посещения {att.train_date.date()}",
            attendance_id=att.id,
            commit=False,
        )
        att.paid_by = PaidBy.BALANCE
        return True
    except InsufficientBalanceError:
        att.paid_by = PaidBy.UNPAID
        return False


async def _load_unpaid_attendances(db: AsyncSession, mmas_id: str) -> List[Attendance]:
    result = await db.execute(
        select(Attendance)
        .join(Student, Student.id == Attendance.student_id)
        .options(*_ATTENDANCE_LOAD)
        .where(and_(Student.mmas_id == mmas_id, Attendance.paid_by == PaidBy.UNPAID))
        .order_by(Attendance.train_date.asc())
    )
    return result.scalars().all()


async def get_unpaid_attendances(db: AsyncSession, mmas_id: str) -> List[Attendance]:
    await get_student_by_mmas_id(db, mmas_id)
    return await _load_unpaid_attendances(db, mmas_id)


async def pay_unpaid_attendances(
    db: AsyncSession,
    mmas_id: str,
    *,
    method: PayMethod = "auto",
) -> List[Attendance]:
    await get_student_by_mmas_id(db, mmas_id)
    unpaid = await _load_unpaid_attendances(db, mmas_id)
    if not unpaid:
        return []

    processed_ids: List[int] = []
    for att in unpaid:
        paid = False
        if method in ("auto", "aboniment"):
            if await try_cover_with_aboniment(db, att):
                paid = True
        if not paid and method in ("auto", "balance"):
            event = await _load_event(db, att.event_id)
            await _charge_from_balance(db, att, event)
        processed_ids.append(att.id)

    await db.commit()
    return await _reload_attendances(db, processed_ids)


async def create_attendance_bulk(
    db: AsyncSession,
    *,
    items: list[tuple[str, str, datetime, int, Optional[str]]],
) -> List[Attendance]:
    created_ids: List[int] = []
    now = datetime.now()

    for mmas_id, studio_short_name, train_dt, hours_int, event_code in items:
        student = await get_student_by_mmas_id(db, mmas_id)
        studio = await get_studio_by_short_name(db, studio_short_name)
        event_obj = await _resolve_event(
            db,
            studio_id=studio.id,
            studio_short_name=studio.short_name,
            event_code=event_code,
        )

        hours_time = time(hour=hours_int, minute=0, second=0)
        att = Attendance(
            student_id=student.id,
            studio_id=studio.id,
            train_date=train_dt,
            hours=hours_time,
            paid_by=PaidBy.UNPAID,
            event_id=event_obj.id,
            created_at=now,
        )
        db.add(att)
        await db.flush()

        covered = await try_cover_with_aboniment(db, att)
        if not covered:
            await _charge_from_balance(db, att, event_obj)
        created_ids.append(att.id)

    await db.commit()
    return await _reload_attendances(db, created_ids)


async def get_attendance_by_date(
    db: AsyncSession,
    *,
    target_date: date,
    studio_short_name: Optional[str] = None,
) -> List[Attendance]:
    filters = [func.date(Attendance.train_date) == target_date]
    if studio_short_name is not None:
        studio = await get_studio_by_short_name(db, studio_short_name)
        filters.append(Attendance.studio_id == studio.id)

    result = await db.execute(
        select(Attendance)
        .options(*_ATTENDANCE_LOAD)
        .where(and_(*filters))
        .order_by(Attendance.train_date.asc())
    )
    return result.scalars().all()


async def _fetch_attendance_in_range(
    db: AsyncSession,
    *,
    from_date: date,
    to_date: date,
    studio_id: Optional[int] = None,
    student_id: Optional[int] = None,
) -> List[Attendance]:
    filters = [
        func.date(Attendance.train_date) >= from_date,
        func.date(Attendance.train_date) <= to_date,
    ]
    if studio_id is not None:
        filters.append(Attendance.studio_id == studio_id)
    if student_id is not None:
        filters.append(Attendance.student_id == student_id)

    result = await db.execute(
        select(Attendance)
        .options(*_ATTENDANCE_LOAD)
        .where(and_(*filters))
        .order_by(Attendance.train_date.asc())
    )
    return result.scalars().all()


async def get_attendance_stats_by_date(
    db: AsyncSession,
    *,
    target_date: date,
    studio_short_name: Optional[str] = None,
) -> tuple[List[Attendance], dict]:
    records = await get_attendance_by_date(
        db, target_date=target_date, studio_short_name=studio_short_name
    )
    return records, _count_by_paid_by(records)


async def get_student_attendance_stats(
    db: AsyncSession,
    *,
    mmas_id: str,
    from_date: date,
    to_date: date,
) -> tuple[Student, List[Attendance]]:
    student = await get_student_by_mmas_id(db, mmas_id)
    records = await _fetch_attendance_in_range(
        db,
        from_date=from_date,
        to_date=to_date,
        student_id=student.id,
    )
    return student, records


async def get_studio_attendance_stats(
    db: AsyncSession,
    *,
    studio_short_name: str,
    from_date: date,
    to_date: date,
) -> tuple[Studio, List[Attendance]]:
    studio = await get_studio_by_short_name(db, studio_short_name)
    records = await _fetch_attendance_in_range(
        db,
        from_date=from_date,
        to_date=to_date,
        studio_id=studio.id,
    )
    return studio, records


def summarize_attendance(records: List[Attendance]) -> dict:
    total_hours = sum(_duration_hours(r.hours) for r in records)
    unpaid = sum(1 for r in records if r.paid_by == PaidBy.UNPAID)
    return {
        "total_visits": len(records),
        "total_hours": round(total_hours, 2),
        "unpaid_count": unpaid,
        "by_paid_by": _count_by_paid_by(records),
    }
