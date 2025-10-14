# Импортируем все модели для правильной работы relationships
from .studios.studio import Studio
from .students.student import Student
from .students.belt import Belt
from .billing.balance_log import BalanceLog
from .billing.pay_log import PayLog
from .billing.aboniment import Aboniment
from .attendance.event import Event
from .attendance.attendance import Attendance
from .accounts.tg_user import TgUser
from .accounts.app_account import AppAccount

__all__ = [
    "Studio", "Student", "Belt",
    "BalanceLog", "PayLog", "Aboniment",
    "Event", "Attendance",
    "TgUser", "AppAccount"
]
