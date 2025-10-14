from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_students():
    """Получение списка студентов"""
    return {"message": "Get students endpoint - to be implemented"}

@router.get("/{student_id}")
async def get_student(student_id: int):
    """Получение студента по ID"""
    return {"message": f"Get student {student_id} endpoint - to be implemented"}

@router.post("/")
async def create_student():
    """Создание нового студента"""
    return {"message": "Create student endpoint - to be implemented"}

@router.put("/{student_id}")
async def update_student(student_id: int):
    """Обновление студента"""
    return {"message": f"Update student {student_id} endpoint - to be implemented"}

@router.delete("/{student_id}")
async def delete_student(student_id: int):
    """Удаление студента"""
    return {"message": f"Delete student {student_id} endpoint - to be implemented"}
