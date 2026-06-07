from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import StaffDep
from app.schemas.accounts import TgLinkRequest, TgUnlinkRequest, TgAccountRead
from app.services.accounts.service import (
    link_tg_account,
    unlink_tg_account,
    list_tg_links,
)

router = APIRouter()


@router.get(
    "/tg/{tg_id}",
    response_model=TgAccountRead,
    summary="Связи Telegram",
    description="Список mmas_id, привязанных к Telegram user id.",
)
async def api_get_tg_links(
    tg_id: int,
    _: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    linked = await list_tg_links(db, tg_id=tg_id)
    return TgAccountRead(tg_id=tg_id, linked_mmas_ids=linked)


@router.post(
    "/tg/link",
    response_model=TgAccountRead,
    summary="Привязать Telegram",
    description="Связывает tg_id со студентом (mmas_id). Staff должен иметь доступ к студии студента.",
)
async def api_link_tg(
    body: TgLinkRequest,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    linked = await link_tg_account(
        db, staff=staff, tg_id=body.tg_id, mmas_id=body.mmas_id
    )
    return TgAccountRead(tg_id=body.tg_id, linked_mmas_ids=linked)


@router.post(
    "/tg/unlink",
    response_model=TgAccountRead,
    summary="Отвязать Telegram",
    description="Удаляет связь tg_id ↔ mmas_id.",
)
async def api_unlink_tg(
    body: TgUnlinkRequest,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    linked = await unlink_tg_account(
        db, staff=staff, tg_id=body.tg_id, mmas_id=body.mmas_id
    )
    return TgAccountRead(tg_id=body.tg_id, linked_mmas_ids=linked)
