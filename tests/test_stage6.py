from app.core.deps import CurrentUser, assert_studio_access
from app.core.exceptions import ForbiddenError
from app.core.jwt import create_access_token, safe_decode_token
import pytest


def test_assert_studio_access_admin():
    admin = CurrentUser(
        subject="admin",
        token_type="staff",
        role="admin",
        studio_short_names=[],
    )
    assert_studio_access(admin, "MSK")


def test_assert_studio_access_trainer_ok():
    trainer = CurrentUser(
        subject="coach",
        token_type="staff",
        role="trainer",
        studio_short_names=["MSK", "SPB"],
    )
    assert_studio_access(trainer, "msk")


def test_assert_studio_access_trainer_denied():
    trainer = CurrentUser(
        subject="coach",
        token_type="staff",
        role="trainer",
        studio_short_names=["MSK"],
    )
    with pytest.raises(ForbiddenError):
        assert_studio_access(trainer, "SPB")


def test_jwt_access_token_roundtrip():
    token = create_access_token(
        subject="coach1",
        token_type="staff",
        role="trainer",
        studios=["MSK", "SPB"],
    )
    payload = safe_decode_token(token)
    assert payload is not None
    assert payload["sub"] == "coach1"
    assert payload["role"] == "trainer"
    assert payload["studios"] == ["MSK", "SPB"]
    assert payload.get("token_kind") is None
