from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.accounts.app_account import AppAccount
    
class TgUser(Base):
    __tablename__ = "tg_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    app_accounts: Mapped[List["AppAccount"]] = relationship("AppAccount", back_populates="tg_user")