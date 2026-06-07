from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.accounts.tg_user import TgUser


class AppAccount(Base):
    __tablename__ = "app_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer, ForeignKey("tg_users.id"), nullable=False)
    mmas_id: Mapped[str] = mapped_column(String(255), nullable=False)

    tg_user: Mapped["TgUser"] = relationship("TgUser", back_populates="app_accounts")