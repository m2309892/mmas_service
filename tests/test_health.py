def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MMAS Service API"
    assert data["version"] == "1.0.0"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_students_balance_not_found(client_db_not_found):
    response = client_db_not_found.get("/api/students/balance/nonexistent-id")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_app_imports():
    from app.core.config import settings
    from app.core.database import Base
    from app.repositories import BaseRepository, StudentRepository
    from app.schemas import StudentRead, AttendanceBulkRequest, BalanceLogRead

    assert settings.app_name == "MMAS Service"
    assert Base is not None
    assert StudentRepository is not None
    assert StudentRead is not None
    assert AttendanceBulkRequest is not None
