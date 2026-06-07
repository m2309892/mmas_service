from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.deps import assert_studio_access, CurrentUser
from app.models.accounts.tg_user import TgUser
from app.models.accounts.app_account import AppAccount
from app.models.students.student import Student
from app.services.students.service import get_student_by_mmas_id


async def _get_or_create_tg_user(db: AsyncSession, tg_id: int) -> TgUser:
    result = await db.execute(select(TgUser).where(TgUser.tg_id == tg_id))
    tg_user = result.scalar_one_or_none()
    if tg_user is None:
        tg_user = TgUser(tg_id=tg_id)
        db.add(tg_user)
        await db.flush()
    return tg_user


async def link_tg_account(
    db: AsyncSession,
    *,
    staff: CurrentUser,
    tg_id: int,
    mmas_id: str,
) -> list[str]:
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)

    tg_user = await _get_or_create_tg_user(db, tg_id)

    existing = await db.execute(
        select(AppAccount).where(
            (AppAccount.tg_id == tg_user.id) & (AppAccount.mmas_id == mmas_id)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Telegram {tg_id} is already linked to {mmas_id}")

    db.add(AppAccount(tg_id=tg_user.id, mmas_id=mmas_id))
    await db.commit()
    return await list_tg_links(db, tg_id=tg_id)


async def unlink_tg_account(
    db: AsyncSession,
    *,
    staff: CurrentUser,
    tg_id: int,
    mmas_id: str,
) -> list[str]:
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)

    result = await db.execute(
        select(TgUser)
        .options(selectinload(TgUser.app_accounts))
        .where(TgUser.tg_id == tg_id)
    )
    tg_user = result.scalar_one_or_none()
    if tg_user is None:
        raise NotFoundError(f"Telegram user {tg_id} not found")

    link = next((a for a in tg_user.app_accounts if a.mmas_id == mmas_id), None)
    if link is None:
        raise NotFoundError(f"Telegram {tg_id} is not linked to {mmas_id}")

    await db.delete(link)
    await db.commit()
    return await list_tg_links(db, tg_id=tg_id)


async def list_tg_links(db: AsyncSession, *, tg_id: int) -> list[str]:
    result = await db.execute(
        select(TgUser)
        .options(selectinload(TgUser.app_accounts))
        .where(TgUser.tg_id == tg_id)
    )
    tg_user = result.scalar_one_or_none()
    if tg_user is None:
        return []
    return [account.mmas_id for account in tg_user.app_accounts]
