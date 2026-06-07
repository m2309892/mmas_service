from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AdminDep
from app.models.accounts.staff_user import StaffRole
from app.schemas.staff import StaffCreate, StaffUpdate, StaffRead
from app.services.staff.service import (
    list_staff_users,
    get_staff_by_username,
    create_staff_user,
    update_staff_user,
)

router = APIRouter()


@router.get(
    "/staff",
    response_model=list[StaffRead],
    summary="Список staff",
    description="Все staff-пользователи с пагинацией. Требуется роль admin.",
)
async def api_list_staff(
    _: AdminDep,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    staff_list = await list_staff_users(db, skip=skip, limit=limit)
    return [StaffRead.from_staff(s) for s in staff_list]


@router.post(
    "/staff",
    response_model=StaffRead,
    status_code=201,
    summary="Создать staff",
    description="Создание admin или trainer. Trainer должен быть привязан минимум к одной студии.",
)
async def api_create_staff(
    body: StaffCreate,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    staff = await create_staff_user(
        db,
        username=body.username,
        password=body.password,
        name=body.name,
        role=StaffRole(body.role),
        studio_short_names=body.studio_short_names,
    )
    return StaffRead.from_staff(staff)


@router.get(
    "/staff/{username}",
    response_model=StaffRead,
    summary="Получить staff",
    description="Профиль staff-пользователя по username.",
)
async def api_get_staff(
    username: str,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    staff = await get_staff_by_username(db, username)
    return StaffRead.from_staff(staff)


@router.put(
    "/staff/{username}",
    response_model=StaffRead,
    summary="Обновить staff",
    description="Изменение имени, пароля, активности и привязки к студиям.",
)
async def api_update_staff(
    username: str,
    body: StaffUpdate,
    _: AdminDep,
    db: AsyncSession = Depends(get_db),
):
    staff = await update_staff_user(
        db,
        username=username,
        name=body.name,
        password=body.password,
        is_active=body.is_active,
        studio_short_names=body.studio_short_names,
    )
    return StaffRead.from_staff(staff)
