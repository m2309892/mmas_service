from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import StaffDep, assert_studio_access
from app.core.exceptions import AppError
from app.schemas.attendance import (
    AttendanceBulkRequest,
    AttendanceRead,
    AttendanceByDateItem,
    PayUnpaidRequest,
    AttendanceStatsByDate,
    StudentAttendanceStats,
    StudioAttendanceStats,
)
from app.services.attendance.service import (
    get_unpaid_attendances,
    create_attendance_bulk,
    get_attendance_by_date,
    pay_unpaid_attendances,
    get_attendance_stats_by_date,
    get_student_attendance_stats,
    get_studio_attendance_stats,
    summarize_attendance,
)
from app.services.students.service import get_student_by_mmas_id

router = APIRouter()


@router.get(
    "/unpaid/{mmas_id}",
    response_model=list[AttendanceRead],
    summary="Неоплаченные визиты",
    description="Посещения со статусом paid_by=unpaid для студента.",
)
async def api_get_unpaid_attendances(mmas_id: str, db: AsyncSession = Depends(get_db)):
    attendances = await get_unpaid_attendances(db, mmas_id)
    return [AttendanceRead.from_attendance(a) for a in attendances]


@router.post(
    "/pay-unpaid/{mmas_id}",
    response_model=list[AttendanceRead],
    summary="Оплатить долги",
    description="Списание с абонемента или баланса за неоплаченные визиты.",
)
async def api_pay_unpaid_attendances(
    mmas_id: str,
    staff: StaffDep,
    body: PayUnpaidRequest = PayUnpaidRequest(),
    db: AsyncSession = Depends(get_db),
):
    student = await get_student_by_mmas_id(db, mmas_id)
    assert_studio_access(staff, student.studio.short_name)
    attendances = await pay_unpaid_attendances(db, mmas_id, method=body.method)
    return [AttendanceRead.from_attendance(a) for a in attendances]


@router.post(
    "/bulk",
    response_model=list[AttendanceRead],
    summary="Массовая отметка",
    description="Создание посещений пакетом. Автооплата с баланса/абонемента при наличии средств.",
)
async def api_create_bulk_attendance(
    body: AttendanceBulkRequest,
    staff: StaffDep,
    db: AsyncSession = Depends(get_db),
):
    for item in body.items:
        assert_studio_access(staff, item.studio_short_name)
    items = [
        (
            item.mmas_id,
            item.studio_short_name,
            item.train_date,
            item.hours,
            item.event_code,
        )
        for item in body.items
    ]
    attendances = await create_attendance_bulk(db, items=items)
    return [AttendanceRead.from_attendance(a) for a in attendances]


@router.get(
    "/by-date",
    response_model=list[AttendanceByDateItem],
    summary="Посещения за дату",
    description="Список визитов на указанную дату с опциональным фильтром по студии.",
)
async def api_get_attendance_by_date(
    target_date: date = Query(..., description="Дата тренировок"),
    studio_short_name: Optional[str] = Query(
        default=None, description="Код студии для фильтрации"
    ),
    db: AsyncSession = Depends(get_db),
):
    records = await get_attendance_by_date(
        db, target_date=target_date, studio_short_name=studio_short_name
    )
    return [
        AttendanceByDateItem(
            mmas_id=r.student.mmas_id,
            studio_short_name=r.studio.short_name,
            event_code=r.event.code,
            hours=r.hours.strftime("%H:%M:%S"),
            paid_by=r.paid_by,
        )
        for r in records
    ]


@router.get(
    "/stats/by-date",
    response_model=AttendanceStatsByDate,
    summary="Статистика за день",
    description="Агрегаты посещаемости и разбивка по способу оплаты.",
)
async def api_stats_by_date(
    target_date: date = Query(..., description="Дата"),
    studio_short_name: Optional[str] = Query(default=None, description="Код студии"),
    db: AsyncSession = Depends(get_db),
):
    records, by_paid_by = await get_attendance_stats_by_date(
        db, target_date=target_date, studio_short_name=studio_short_name
    )
    summary = summarize_attendance(records)
    return AttendanceStatsByDate(
        target_date=target_date,
        studio_short_name=studio_short_name,
        total_visits=summary["total_visits"],
        total_hours=summary["total_hours"],
        unpaid_count=summary["unpaid_count"],
        by_paid_by=by_paid_by,
        items=[AttendanceRead.from_attendance(r) for r in records],
    )


@router.get(
    "/stats/student/{mmas_id}",
    response_model=StudentAttendanceStats,
    summary="Статистика студента",
    description="Посещаемость студента за период from_date — to_date.",
)
async def api_stats_student(
    mmas_id: str,
    from_date: date = Query(..., description="Начало периода (включительно)"),
    to_date: date = Query(..., description="Конец периода (включительно)"),
    db: AsyncSession = Depends(get_db),
):
    if from_date > to_date:
        raise AppError("from_date must be before or equal to to_date")
    _, records = await get_student_attendance_stats(
        db, mmas_id=mmas_id, from_date=from_date, to_date=to_date
    )
    summary = summarize_attendance(records)
    return StudentAttendanceStats(
        mmas_id=mmas_id,
        from_date=from_date,
        to_date=to_date,
        total_visits=summary["total_visits"],
        total_hours=summary["total_hours"],
        unpaid_count=summary["unpaid_count"],
        by_paid_by=summary["by_paid_by"],
    )


@router.get(
    "/stats/studio/{studio_short_name}",
    response_model=StudioAttendanceStats,
    summary="Статистика студии",
    description="Посещаемость студии за период: визиты, уникальные студенты, часы.",
)
async def api_stats_studio(
    studio_short_name: str,
    from_date: date = Query(..., description="Начало периода"),
    to_date: date = Query(..., description="Конец периода"),
    db: AsyncSession = Depends(get_db),
):
    if from_date > to_date:
        raise AppError("from_date must be before or equal to to_date")
    studio, records = await get_studio_attendance_stats(
        db,
        studio_short_name=studio_short_name,
        from_date=from_date,
        to_date=to_date,
    )
    summary = summarize_attendance(records)
    unique_students = len({r.student_id for r in records})
    return StudioAttendanceStats(
        studio_short_name=studio.short_name,
        from_date=from_date,
        to_date=to_date,
        total_visits=summary["total_visits"],
        unique_students=unique_students,
        total_hours=summary["total_hours"],
        unpaid_count=summary["unpaid_count"],
        by_paid_by=summary["by_paid_by"],
    )
