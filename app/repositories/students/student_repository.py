from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from .base_repository import BaseRepository
from app.models.student import Student


class StudentRepository(BaseRepository[Student]):
    """Репозиторий для работы со студентами"""
    
    def __init__(self):
        super().__init__(Student)
    
    async def get_by_telegram_id(self, db: AsyncSession, telegram_id: int) -> Optional[Student]:
        """Получить студента по Telegram ID"""
        return await self.get_by_field(db, "telegram_id", telegram_id)
    
    async def get_by_telegram_username(self, db: AsyncSession, username: str) -> Optional[Student]:
        """Получить студента по Telegram username"""
        return await self.get_by_field(db, "telegram_username", username)
    
    async def get_by_creator(self, db: AsyncSession, creator_id: int, skip: int = 0, limit: int = 100) -> List[Student]:
        """Получить студентов, созданных конкретным пользователем"""
        result = await db.execute(
            select(Student)
            .where(Student.created_by == creator_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_by_name(self, db: AsyncSession, name: str, skip: int = 0, limit: int = 100) -> List[Student]:
        """Поиск студентов по имени"""
        search_term = f"%{name}%"
        result = await db.execute(
            select(Student)
            .where(
                and_(
                    Student.is_active == True,
                    (
                        Student.first_name.ilike(search_term) |
                        Student.last_name.ilike(search_term) |
                        Student.middle_name.ilike(search_term)
                    )
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_students(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Student]:
        """Получить только активных студентов"""
        result = await db.execute(
            select(Student)
            .where(Student.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
