from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance.attendance import Attendance, PaidBy
from app.models.attendance.event import Event
from app.models.billing.aboniment import Aboniment


def attendance_duration_hours(att: Attendance) -> float:
    return att.hours.hour + att.hours.minute / 60.0


def calculate_attendance_price(event: Event, att: Attendance) -> Decimal:
    duration = attendance_duration_hours(att)
    return Decimal(str(float(event.price) * duration))


async def get_applicable_aboniments(
    db: AsyncSession,
    *,
    student_id: int,
    studio_id: int,
    train_date: date,
) -> List[Aboniment]:
    result = await db.execute(
        select(Aboniment)
        .where(
            and_(
                Aboniment.studio_id == studio_id,
                Aboniment.student_id == student_id,
                Aboniment.end_date >= train_date,
            )
        )
        .order_by(Aboniment.end_date.asc())
    )
    return result.scalars().all()


async def try_cover_with_aboniment(db: AsyncSession, att: Attendance) -> bool:
    aboniments = await get_applicable_aboniments(
        db,
        student_id=att.student_id,
        studio_id=att.studio_id,
        train_date=att.train_date.date(),
    )
    if not aboniments:
        return False

    duration_hours = attendance_duration_hours(att)

    for ab in aboniments:
        if ab.hours is not None and ab.hours > 0:
            if ab.hours >= duration_hours:
                ab.hours = int(ab.hours - duration_hours)
                att.paid_by = PaidBy.H_ABONIMENT
                return True
        elif ab.hours is None:
            att.paid_by = PaidBy.T_ABONEMENT
            return True

    return False
