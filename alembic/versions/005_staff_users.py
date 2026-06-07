"""staff users and multi-studio assignments

Revision ID: 005
Revises: 004
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

staff_role_enum = sa.Enum("admin", "trainer", name="staffrole")


def upgrade() -> None:
    op.create_table(
        "staff_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", staff_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "staff_user_studios",
        sa.Column("staff_user_id", sa.Integer(), nullable=False),
        sa.Column("studio_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["staff_user_id"], ["staff_users.id"]),
        sa.ForeignKeyConstraint(["studio_id"], ["studios.id"]),
        sa.PrimaryKeyConstraint("staff_user_id", "studio_id"),
    )


def downgrade() -> None:
    op.drop_table("staff_user_studios")
    op.drop_table("staff_users")
    staff_role_enum.drop(op.get_bind(), checkfirst=True)
