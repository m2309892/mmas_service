from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AdminDep
from app.schemas.studios import StudioCreate, StudioUpdate, StudioRead
from app.services.studios.service import (
    list_studios,
    get_studio_by_short_name,
    create_studio,
    update_studio,
    delete_studio,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[StudioRead],
    summary="Список студий",
    description="Все студии сети. Доступно без авторизации.",
)
async def api_list_studios(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    studios = await list_studios(db, skip=skip, limit=limit)
    return [StudioRead.from_studio(s) for s in studios]


@router.post(
    "/",
    response_model=StudioRead,
    status_code=201,
    summary="Создать студию",
    description="Регистрация новой студии. short_name уникален и используется в API.",
)
async def api_create_studio(
    body: StudioCreate,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    studio = await create_studio(db, name=body.name, short_name=body.short_name)
    return StudioRead.from_studio(studio)


@router.get(
    "/{short_name}",
    response_model=StudioRead,
    summary="Получить студию",
    description="Карточка студии по публичному коду short_name.",
)
async def api_get_studio(short_name: str, db: AsyncSession = Depends(get_db)):
    studio = await get_studio_by_short_name(db, short_name)
    return StudioRead.from_studio(studio)


@router.put(
    "/{short_name}",
    response_model=StudioRead,
    summary="Обновить студию",
    description="Изменение отображаемого названия. short_name не меняется.",
)
async def api_update_studio(
    short_name: str,
    body: StudioUpdate,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    studio = await update_studio(db, short_name=short_name, name=body.name)
    return StudioRead.from_studio(studio)


@router.delete(
    "/{short_name}",
    status_code=204,
    summary="Удалить студию",
    description="Удаление студии. Ошибка, если есть связанные студенты.",
)
async def api_delete_studio(
    short_name: str,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    await delete_studio(db, short_name=short_name)
