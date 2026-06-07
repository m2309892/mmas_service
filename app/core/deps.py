from dataclasses import dataclass
from typing import Annotated, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, AppError
from app.core.jwt import safe_decode_token
from app.models.accounts.staff_user import StaffRole

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    subject: str
    token_type: str
    role: str
    studio_short_names: list[str]

    @property
    def is_admin(self) -> bool:
        return self.role == StaffRole.ADMIN.value

    @property
    def is_trainer(self) -> bool:
        return self.role == StaffRole.TRAINER.value

    @property
    def is_staff(self) -> bool:
        return self.token_type == "staff"


def _user_from_payload(payload: dict) -> CurrentUser:
    return CurrentUser(
        subject=payload["sub"],
        token_type=payload["type"],
        role=payload["role"],
        studio_short_names=[s.upper() for s in payload.get("studios", [])],
    )


async def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
) -> Optional[CurrentUser]:
    if credentials is None:
        return None
    payload = safe_decode_token(credentials.credentials)
    if payload is None or payload.get("token_kind") == "refresh":
        return None
    return _user_from_payload(payload)


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
) -> CurrentUser:
    if credentials is None:
        raise AppError("Not authenticated", status_code=401)
    payload = safe_decode_token(credentials.credentials)
    if payload is None or payload.get("token_kind") == "refresh":
        raise AppError("Invalid or expired token", status_code=401)
    return _user_from_payload(payload)


async def get_current_staff(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not user.is_staff:
        raise ForbiddenError("Staff access required")
    return user


def require_staff_roles(*roles: StaffRole):
    allowed = {role.value for role in roles}

    async def _check(user: Annotated[CurrentUser, Depends(get_current_staff)]) -> CurrentUser:
        if user.role not in allowed:
            raise ForbiddenError(f"Requires one of roles: {', '.join(sorted(allowed))}")
        return user

    return _check


def assert_studio_access(user: CurrentUser, studio_short_name: str) -> None:
    if user.is_admin:
        return
    if user.is_trainer:
        normalized = studio_short_name.strip().upper()
        if normalized not in user.studio_short_names:
            raise ForbiddenError(
                f"No access to studio {studio_short_name}. "
                f"Your studios: {', '.join(user.studio_short_names) or 'none'}"
            )
        return
    raise ForbiddenError("Staff access required for this studio")


StaffUserDep = Annotated[CurrentUser, Depends(get_current_staff)]
AdminDep = Annotated[CurrentUser, Depends(require_staff_roles(StaffRole.ADMIN))]
StaffDep = Annotated[
    CurrentUser, Depends(require_staff_roles(StaffRole.ADMIN, StaffRole.TRAINER))
]
