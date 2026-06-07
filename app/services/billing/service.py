from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, NotFoundError
from app.models.billing.aboniment import Aboniment
from app.models.studios.studio import Studio
from app.services.billing.balance_service import debit
from app.services.studios.service import get_studio_by_short_name
from app.services.students.service import get_student_by_mmas_id


def validate_aboniment_params(*, end_date: date, hours: Optional[int]) -> None:
    if end_date < date.today():
        raise AppError("end_date must be today or in the future")
    if hours is not None and hours <= 0:
        raise AppError("hours must be a positive integer, or omit for unlimited")


async def _upsert_aboniment(
    db: AsyncSession,
    *,
    student_id: int,
    studio_id: int,
    end_date: date,
    hours: Optional[int],
) -> Aboniment:
    result = await db.execute(
        select(Aboniment)
        .where(
            (Aboniment.student_id == student_id) & (Aboniment.studio_id == studio_id)
        )
        .order_by(Aboniment.end_date.desc())
        .limit(1)
    )
    aboniment = result.scalar_one_or_none()

    if aboniment is None:
        aboniment = Aboniment(
            student_id=student_id,
            studio_id=studio_id,
            hours=hours,
            end_date=end_date,
        )
        db.add(aboniment)
    else:
        aboniment.end_date = end_date
        aboniment.hours = hours

    return aboniment


async def list_aboniments_by_mmas_id(db: AsyncSession, mmas_id: str) -> List[Aboniment]:
    student = await get_student_by_mmas_id(db, mmas_id)
    result = await db.execute(
        select(Aboniment)
        .options(selectinload(Aboniment.studio))
        .where(Aboniment.student_id == student.id)
        .order_by(Aboniment.end_date.desc())
    )
    return result.scalars().all()


async def get_aboniment_by_studio(
    db: AsyncSession, *, mmas_id: str, studio_short_name: str
) -> Aboniment:
    student = await get_student_by_mmas_id(db, mmas_id)
    studio = await get_studio_by_short_name(db, studio_short_name)
    result = await db.execute(
        select(Aboniment)
        .options(selectinload(Aboniment.studio))
        .where(
            (Aboniment.student_id == student.id) & (Aboniment.studio_id == studio.id)
        )
        .order_by(Aboniment.end_date.desc())
        .limit(1)
    )
    aboniment = result.scalar_one_or_none()
    if aboniment is None:
        raise NotFoundError(
            f"Aboniment for mmas_id={mmas_id} and studio={studio_short_name} not found"
        )
    return aboniment


async def grant_aboniment(
    db: AsyncSession,
    *,
    mmas_id: str,
    studio_short_name: str,
    end_date: date,
    hours: Optional[int] = None,
) -> Aboniment:
    validate_aboniment_params(end_date=end_date, hours=hours)
    student = await get_student_by_mmas_id(db, mmas_id)
    studio = await get_studio_by_short_name(db, studio_short_name)

    aboniment = await _upsert_aboniment(
        db,
        student_id=student.id,
        studio_id=studio.id,
        end_date=end_date,
        hours=hours,
    )
    await db.commit()
    await db.refresh(aboniment)
    result = await db.execute(
        select(Aboniment)
        .options(selectinload(Aboniment.studio))
        .where(Aboniment.id == aboniment.id)
    )
    return result.scalar_one()


async def purchase_aboniment_from_balance(
    db: AsyncSession,
    *,
    mmas_id: str,
    studio_short_name: str,
    end_date: date,
    hours: Optional[int],
    price: Decimal,
    comment: Optional[str] = None,
) -> Aboniment:
    validate_aboniment_params(end_date=end_date, hours=hours)
    student = await get_student_by_mmas_id(db, mmas_id)
    studio = await get_studio_by_short_name(db, studio_short_name)

    aboniment = await _upsert_aboniment(
        db,
        student_id=student.id,
        studio_id=studio.id,
        end_date=end_date,
        hours=hours,
    )
    await db.flush()
    await db.refresh(aboniment)

    default_comment = f"Покупка абонемента {studio.short_name} до {end_date}"
    await debit(
        db,
        student_id=student.id,
        amount=price,
        comment=comment or default_comment,
        aboniment_id=aboniment.id,
        commit=False,
    )
    await db.commit()

    result = await db.execute(
        select(Aboniment)
        .options(selectinload(Aboniment.studio))
        .where(Aboniment.id == aboniment.id)
    )
    return result.scalar_one()


async def add_or_update_aboniment(
    db: AsyncSession,
    *,
    mmas_id: str,
    studio_short_name: str,
    end_date: date,
    hours: Optional[int] = None,
) -> Aboniment:
    return await grant_aboniment(
        db,
        mmas_id=mmas_id,
        studio_short_name=studio_short_name,
        end_date=end_date,
        hours=hours,
    )
