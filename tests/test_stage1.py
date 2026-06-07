from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.security import hash_password, verify_password
from app.schemas.belts import BeltRead
from app.schemas.studios import StudioRead
from app.schemas.students import StudentRead
from app.services.students.service import generate_mmas_id


def test_hash_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


@pytest.mark.asyncio
async def test_generate_mmas_id_first():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.all.return_value = []
    db.execute = AsyncMock(return_value=result_mock)

    studio = MagicMock()
    studio.id = 1
    studio.short_name = "MSK"

    mmas_id = await generate_mmas_id(db, studio)
    assert mmas_id == "MSK-0001"


@pytest.mark.asyncio
async def test_generate_mmas_id_increments():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.all.return_value = [("MSK-0001",), ("MSK-0003",)]
    db.execute = AsyncMock(return_value=result_mock)

    studio = MagicMock()
    studio.id = 1
    studio.short_name = "MSK"

    mmas_id = await generate_mmas_id(db, studio)
    assert mmas_id == "MSK-0004"


def test_student_read_schema_has_no_internal_id():
    fields = set(StudentRead.model_fields.keys())
    assert "id" not in fields
    assert "hashed_password" not in fields
    assert "mmas_id" in fields
    assert "studio_short_name" in fields


def test_studio_read_schema_has_no_internal_id():
    fields = set(StudioRead.model_fields.keys())
    assert "id" not in fields
    assert "short_name" in fields


def test_belt_read_schema_has_no_internal_id():
    fields = set(BeltRead.model_fields.keys())
    assert "id" not in fields
    assert "code" in fields
