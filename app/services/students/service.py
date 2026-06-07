from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.models.students.student import Student
from app.models.studios.studio import Studio
from app.models.accounts.tg_user import TgUser
from app.models.accounts.app_account import AppAccount
from app.models.students.belt import Belt
from app.models.billing.balance_log import BalanceLog
from app.services.studios.service import get_studio_by_short_name, recalc_students_cnt
from app.services.belts.service import get_belt_by_code


def _student_load_options():
    return selectinload(Student.studio), selectinload(Student.belt)


async def generate_mmas_id(db: AsyncSession, studio: Studio) -> str:
    prefix = f"{studio.short_name.upper()}-"
    result = await db.execute(
        select(Student.mmas_id).where(Student.studio_id == studio.id)
    )
    max_seq = 0
    for (existing_id,) in result.all():
        if existing_id.startswith(prefix):
            suffix = existing_id[len(prefix) :]
            if suffix.isdigit():
                max_seq = max(max_seq, int(suffix))
    return f"{prefix}{max_seq + 1:04d}"


async def get_student_by_mmas_id(db: AsyncSession, mmas_id: str) -> Student:
    result = await db.execute(
        select(Student)
        .options(*_student_load_options())
        .where(Student.mmas_id == mmas_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise NotFoundError(f"Student with mmas_id={mmas_id} not found")
    return student


async def create_student(
    db: AsyncSession,
    *,
    name: str,
    password: str,
    birth_date: datetime,
    gender: str,
    studio_short_name: str,
    belt_code: str,
) -> Student:
    studio = await get_studio_by_short_name(db, studio_short_name)
    belt = await get_belt_by_code(db, belt_code)
    mmas_id = await generate_mmas_id(db, studio)
    now = datetime.now()

    student = Student(
        name=name,
        hashed_password=hash_password(password),
        birth_date=birth_date,
        gender=gender,
        balance=0,
        mmas_id=mmas_id,
        studio_id=studio.id,
        belt_id=belt.id,
        created_at=now,
        updated_at=now,
    )
    db.add(student)
    await db.flush()
    await recalc_students_cnt(db, studio.id)
    await db.commit()

    return await get_student_by_mmas_id(db, mmas_id)


async def update_student(
    db: AsyncSession,
    *,
    mmas_id: str,
    name: Optional[str] = None,
    password: Optional[str] = None,
    birth_date: Optional[datetime] = None,
    gender: Optional[str] = None,
    belt_code: Optional[str] = None,
) -> Student:
    student = await get_student_by_mmas_id(db, mmas_id)

    if name is not None:
        student.name = name
    if password is not None:
        student.hashed_password = hash_password(password)
    if birth_date is not None:
        student.birth_date = birth_date
    if gender is not None:
        student.gender = gender
    if belt_code is not None:
        belt = await get_belt_by_code(db, belt_code)
        student.belt_id = belt.id

    student.updated_at = datetime.now()
    await db.commit()
    return await get_student_by_mmas_id(db, mmas_id)


async def delete_student(db: AsyncSession, *, mmas_id: str) -> None:
    student = await get_student_by_mmas_id(db, mmas_id)
    studio_id = student.studio_id
    await db.delete(student)
    await db.flush()
    await recalc_students_cnt(db, studio_id)
    await db.commit()


async def get_balance_by_tg_id(db: AsyncSession, tg_id: int) -> List[Tuple[str, int]]:
    result = await db.execute(
        select(AppAccount.mmas_id, Student.balance)
        .join(TgUser, TgUser.id == AppAccount.tg_id)
        .join(Student, Student.mmas_id == AppAccount.mmas_id)
        .where(TgUser.tg_id == tg_id)
    )
    rows = result.all()
    return [(mid, int(balance)) for mid, balance in rows]


async def list_students_with_filters(
    db: AsyncSession,
    *,
    studio_short_name: Optional[str] = None,
    belt_code: Optional[str] = None,
    name_substring: Optional[str] = None,
    mmas_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Student]:
    stmt = select(Student).options(*_student_load_options())

    filters = []
    if studio_short_name is not None:
        stmt = stmt.join(Studio, Studio.id == Student.studio_id)
        filters.append(Studio.short_name == studio_short_name)
    if belt_code is not None:
        stmt = stmt.join(Belt, Belt.id == Student.belt_id)
        filters.append(Belt.code == belt_code)
    if name_substring:
        filters.append(Student.name.ilike(f"%{name_substring}%"))
    if mmas_id:
        filters.append(Student.mmas_id == mmas_id)
    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def list_students_projection(
    db: AsyncSession,
    *,
    studio_short_name: Optional[str] = None,
    belt_code: Optional[str] = None,
    name_substring: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[tuple]:
    filters = []
    if studio_short_name is not None:
        filters.append(Studio.short_name == studio_short_name)
    if belt_code is not None:
        filters.append(Belt.code == belt_code)
    if name_substring:
        filters.append(Student.name.ilike(f"%{name_substring}%"))

    stmt = (
        select(Student.mmas_id, Student.name, Belt.color)
        .join(Belt, Belt.id == Student.belt_id)
        .join(Studio, Studio.id == Student.studio_id)
    )
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.all()


async def get_balance_history_by_mmas_id(
    db: AsyncSession,
    mmas_id: str,
    *,
    skip: int = 0,
    limit: int = 100,
) -> List[BalanceLog]:
    student = await get_student_by_mmas_id(db, mmas_id)
    stmt = (
        select(BalanceLog)
        .where(BalanceLog.student_id == student.id)
        .order_by(BalanceLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_balance_by_mmas_id(db: AsyncSession, mmas_id: str) -> int:
    student = await get_student_by_mmas_id(db, mmas_id)
    return int(student.balance)
