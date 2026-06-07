from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import StaffDep, assert_studio_access
from app.schemas.events import EventCreate, EventUpdate, EventRead
from app.services.events.service import (
    list_events,
    get_event_by_code,
    create_event,
    update_event,
    delete_event,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[EventRead],
    summary="Список занятий",
    description="Типы занятий с ценами. Фильтр по studio_short_name опционален.",
)
async def api_list_events(
    studio_short_name: Optional[str] = Query(
        default=None, description="Код студии для фильтрации"
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    events = await list_events(
        db, studio_short_name=studio_short_name, skip=skip, limit=limit
    )
    return [EventRead.from_event(e) for e in events]


@router.post(
    "/",
    response_model=EventRead,
    status_code=201,
    summary="Создать занятие",
    description="Новый тип занятия в студии. code уникален в рамках студии.",
)
async def api_create_event(
    body: EventCreate,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    assert_studio_access(staff, body.studio_short_name)
    event = await create_event(
        db,
        studio_short_name=body.studio_short_name,
        code=body.code,
        type=body.type,
        price=body.price,
        description=body.description,
    )
    return EventRead.from_event(event)


@router.get(
    "/{studio_short_name}/{code}",
    response_model=EventRead,
    summary="Получить занятие",
    description="Занятие по паре studio_short_name + code.",
)
async def api_get_event(
    studio_short_name: str,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    event = await get_event_by_code(db, studio_short_name=studio_short_name, code=code)
    return EventRead.from_event(event)


@router.put(
    "/{studio_short_name}/{code}",
    response_model=EventRead,
    summary="Обновить занятие",
    description="Изменение типа, цены или описания.",
)
async def api_update_event(
    studio_short_name: str,
    code: str,
    body: EventUpdate,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    assert_studio_access(staff, studio_short_name)
    event = await update_event(
        db,
        studio_short_name=studio_short_name,
        code=code,
        type=body.type,
        price=body.price,
        description=body.description,
    )
    return EventRead.from_event(event)


@router.delete(
    "/{studio_short_name}/{code}",
    status_code=204,
    summary="Удалить занятие",
    description="Удаление типа занятия. Ошибка при наличии посещений.",
)
async def api_delete_event(
    studio_short_name: str,
    code: str,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    assert_studio_access(staff, studio_short_name)
    await delete_event(db, studio_short_name=studio_short_name, code=code)
