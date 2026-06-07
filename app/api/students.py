from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import StaffDep, assert_studio_access
from app.schemas.students import (
    StudentCreate,
    StudentUpdate,
    StudentRead,
    StudentProjection,
    BalanceByTgItem,
    BalanceResponse,
)
from app.schemas.balance import BalanceAdjustRequest, BalanceLogRead
from app.services.billing.balance_service import (
    credit_by_mmas_id,
    debit_by_mmas_id,
    refund_by_mmas_id,
)
from app.services.students.service import (
    get_balance_by_tg_id,
    list_students_with_filters,
    list_students_projection,
    get_balance_history_by_mmas_id,
    get_balance_by_mmas_id,
    create_student,
    get_student_by_mmas_id,
    update_student,
    delete_student,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[StudentRead],
    summary="Список студентов",
    description="Фильтрация по студии, поясу, имени и mmas_id. Доступно без авторизации.",
)
async def get_students(
    studio_short_name: Optional[str] = Query(
        default=None, description="Код студии, например MSK"
    ),
    belt_code: Optional[str] = Query(default=None, description="Код пояса"),
    name: Optional[str] = Query(default=None, description="Подстрока в имени"),
    mmas_id: Optional[str] = Query(default=None, description="Точный mmas_id"),
    skip: int = Query(default=0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(default=100, ge=1, le=500, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
):
    students = await list_students_with_filters(
        db,
        studio_short_name=studio_short_name,
        belt_code=belt_code,
        name_substring=name,
        mmas_id=mmas_id,
        skip=skip,
        limit=limit,
    )
    return [StudentRead.from_student(s) for s in students]


@router.get(
    "/projection",
    response_model=list[StudentProjection],
    summary="Краткий список студентов",
    description="Облегчённая проекция: mmas_id, имя, цвет пояса.",
)
async def get_students_projection(
    studio_short_name: Optional[str] = Query(default=None, description="Код студии"),
    belt_code: Optional[str] = Query(default=None, description="Код пояса"),
    name: Optional[str] = Query(default=None, description="Подстрока в имени"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_students_projection(
        db,
        studio_short_name=studio_short_name,
        belt_code=belt_code,
        name_substring=name,
        skip=skip,
        limit=limit,
    )
    return [StudentProjection.from_row(row) for row in rows]


@router.get(
    "/balance/by-tg/{tg_id}",
    response_model=list[BalanceByTgItem],
    summary="Баланс по Telegram",
    description="Балансы всех студентов, привязанных к tg_id.",
)
async def api_get_balance_by_tg_id(tg_id: int, db: AsyncSession = Depends(get_db)):
    rows = await get_balance_by_tg_id(db, tg_id)
    return [BalanceByTgItem(mmas_id=m, balance=b) for m, b in rows]


@router.get(
    "/balance/{mmas_id}",
    response_model=BalanceResponse,
    summary="Текущий баланс",
    description="Баланс студента в рублях (целое число).",
)
async def api_get_balance_by_mmas_id(mmas_id: str, db: AsyncSession = Depends(get_db)):
    balance = await get_balance_by_mmas_id(db, mmas_id)
    return BalanceResponse(mmas_id=mmas_id, balance=balance)


@router.get(
    "/balance/history/{mmas_id}",
    response_model=list[BalanceLogRead],
    summary="История баланса",
    description="Журнал операций credit/debit/refund с указанием источника.",
)
async def api_get_balance_history(
    mmas_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    logs = await get_balance_history_by_mmas_id(db, mmas_id, skip=skip, limit=limit)
    return [BalanceLogRead.from_log(log, mmas_id) for log in logs]


@router.post(
    "/balance/{mmas_id}/credit",
    response_model=BalanceLogRead,
    status_code=201,
    summary="Пополнить баланс",
    description="Зачисление средств staff. Требуется доступ к студии студента.",
)
async def api_credit_balance(
    mmas_id: str,
    body: BalanceAdjustRequest,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    log = await credit_by_mmas_id(
        db, mmas_id=mmas_id, amount=body.amount, comment=body.comment
    )
    return BalanceLogRead.from_log(log, mmas_id)


@router.post(
    "/balance/{mmas_id}/debit",
    response_model=BalanceLogRead,
    status_code=201,
    summary="Списать с баланса",
    description="Списание средств. Ошибка при недостаточном балансе.",
)
async def api_debit_balance(
    mmas_id: str,
    body: BalanceAdjustRequest,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    log = await debit_by_mmas_id(
        db, mmas_id=mmas_id, amount=body.amount, comment=body.comment
    )
    return BalanceLogRead.from_log(log, mmas_id)


@router.post(
    "/balance/{mmas_id}/refund",
    response_model=BalanceLogRead,
    status_code=201,
    summary="Возврат на баланс",
    description="Возврат средств студенту (операция refund).",
)
async def api_refund_balance(
    mmas_id: str,
    body: BalanceAdjustRequest,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    log = await refund_by_mmas_id(
        db, mmas_id=mmas_id, amount=body.amount, comment=body.comment
    )
    return BalanceLogRead.from_log(log, mmas_id)


@router.post(
    "/",
    response_model=StudentRead,
    status_code=201,
    summary="Создать студента",
    description="Регистрация студента. mmas_id генерируется автоматически.",
)
async def api_create_student(
    body: StudentCreate,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    assert_studio_access(staff, body.studio_short_name)
    student = await create_student(
        db,
        name=body.name,
        password=body.password,
        birth_date=body.birth_date,
        gender=body.gender,
        studio_short_name=body.studio_short_name,
        belt_code=body.belt_code,
    )
    return StudentRead.from_student(student)


@router.get(
    "/{mmas_id}",
    response_model=StudentRead,
    summary="Получить студента",
    description="Полная карточка студента по mmas_id.",
)
async def api_get_student(mmas_id: str, db: AsyncSession = Depends(get_db)):
    student = await get_student_by_mmas_id(db, mmas_id)
    return StudentRead.from_student(student)


@router.put(
    "/{mmas_id}",
    response_model=StudentRead,
    summary="Обновить студента",
    description="Изменение профиля и пароля. Студию сменить нельзя.",
)
async def api_update_student(
    mmas_id: str,
    body: StudentUpdate,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    student = await update_student(
        db,
        mmas_id=mmas_id,
        name=body.name,
        password=body.password,
        birth_date=body.birth_date,
        gender=body.gender,
        belt_code=body.belt_code,
    )
    return StudentRead.from_student(student)


@router.delete(
    "/{mmas_id}",
    status_code=204,
    summary="Удалить студента",
    description="Удаление студента и связанных данных.",
)
async def api_delete_student(
    mmas_id: str,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    await delete_student(db, mmas_id=mmas_id)
