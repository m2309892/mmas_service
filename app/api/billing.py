from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import StaffDep, assert_studio_access
from app.schemas.billing import AbonimentCreate, AbonimentPurchase, AbonimentRead
from app.services.billing.service import (
    grant_aboniment,
    purchase_aboniment_from_balance,
    list_aboniments_by_mmas_id,
    get_aboniment_by_studio,
)
from app.services.students.service import get_student_by_mmas_id

router = APIRouter()


@router.get(
    "/aboniment/{mmas_id}",
    response_model=list[AbonimentRead],
    summary="Абонементы студента",
    description="Все абонементы студента по всем студиям.",
)
async def api_list_aboniments(mmas_id: str, db: AsyncSession = Depends(get_db)):
    aboniments = await list_aboniments_by_mmas_id(db, mmas_id)
    return [AbonimentRead.from_aboniment(ab, mmas_id=mmas_id) for ab in aboniments]


@router.get(
    "/aboniment/{mmas_id}/{studio_short_name}",
    response_model=AbonimentRead,
    summary="Абонемент в студии",
    description="Абонемент студента в конкретной студии.",
)
async def api_get_aboniment(
    mmas_id: str,
    studio_short_name: str,
    db: AsyncSession = Depends(get_db),
):
    aboniment = await get_aboniment_by_studio(
        db, mmas_id=mmas_id, studio_short_name=studio_short_name
    )
    return AbonimentRead.from_aboniment(aboniment, mmas_id=mmas_id)


@router.post(
    "/aboniment/{mmas_id}",
    response_model=AbonimentRead,
    status_code=201,
    summary="Выдать абонемент",
    description="Бесплатная выдача или продление staff без списания с баланса.",
)
async def api_grant_aboniment(
    mmas_id: str,
    body: AbonimentCreate,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    assert_studio_access(staff, body.studio_short_name)
    aboniment = await grant_aboniment(
        db,
        mmas_id=mmas_id,
        studio_short_name=body.studio_short_name,
        end_date=body.end_date,
        hours=body.hours,
    )
    return AbonimentRead.from_aboniment(aboniment, mmas_id=mmas_id)


@router.post(
    "/aboniment/{mmas_id}/purchase",
    response_model=AbonimentRead,
    status_code=201,
    summary="Купить абонемент",
    description="Покупка с баланса студента: списание price и создание/обновление абонемента.",
)
async def api_purchase_aboniment(
    mmas_id: str,
    body: AbonimentPurchase,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    assert_studio_access(staff, body.studio_short_name)
    aboniment = await purchase_aboniment_from_balance(
        db,
        mmas_id=mmas_id,
        studio_short_name=body.studio_short_name,
        end_date=body.end_date,
        hours=body.hours,
        price=body.price,
        comment=body.comment,
    )
    return AbonimentRead.from_aboniment(aboniment, mmas_id=mmas_id)
