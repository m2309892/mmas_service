from app.models.students.student import Student
from ..base_repository import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self):
        super().__init__(Student)
