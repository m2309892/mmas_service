from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AdminDep
from app.schemas.belts import BeltCreate, BeltUpdate, BeltRead
from app.services.belts.service import (
    list_belts,
    get_belt_by_code,
    create_belt,
    update_belt,
    delete_belt,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[BeltRead],
    summary="Список поясов",
    description="Справочник поясов, отсортированный по sort_order.",
)
async def api_list_belts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    belts = await list_belts(db, skip=skip, limit=limit)
    return [BeltRead.from_belt(b) for b in belts]


@router.post(
    "/",
    response_model=BeltRead,
    status_code=201,
    summary="Создать пояс",
    description="Добавление пояса в справочник. code уникален.",
)
async def api_create_belt(
    body: BeltCreate,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    belt = await create_belt(
        db,
        code=body.code,
        color=body.color,
        style=body.style,
        sort_order=body.sort_order,
    )
    return BeltRead.from_belt(belt)


@router.get(
    "/{code}",
    response_model=BeltRead,
    summary="Получить пояс",
    description="Пояс по публичному коду, например white или blue.",
)
async def api_get_belt(code: str, db: AsyncSession = Depends(get_db)):
    belt = await get_belt_by_code(db, code)
    return BeltRead.from_belt(belt)


@router.put(
    "/{code}",
    response_model=BeltRead,
    summary="Обновить пояс",
    description="Изменение цвета, стиля или порядка сортировки.",
)
async def api_update_belt(
    code: str,
    body: BeltUpdate,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    belt = await update_belt(
        db,
        code=code,
        color=body.color,
        style=body.style,
        sort_order=body.sort_order,
    )
    return BeltRead.from_belt(belt)


@router.delete(
    "/{code}",
    status_code=204,
    summary="Удалить пояс",
    description="Удаление пояса. Ошибка, если есть студенты с этим поясом.",
)
async def api_delete_belt(
    code: str,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    await delete_belt(db, code=code)
