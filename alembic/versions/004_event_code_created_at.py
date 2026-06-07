"""event code and created_at columns

Revision ID: 004
Revises: 003
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("code", sa.String(length=50), nullable=True))
    op.execute(
        sa.text(
            "UPDATE events SET code = LOWER(REPLACE(type, ' ', '-')) WHERE code IS NULL"
        )
    )
    op.alter_column("events", "code", nullable=False)
    op.create_unique_constraint("uq_events_studio_code", "events", ["studio_id", "code"])

    op.add_column(
        "events",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.alter_column("events", "created_at", server_default=None)

    op.add_column(
        "attendance",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.alter_column("attendance", "created_at", server_default=None)


def downgrade() -> None:
    op.drop_column("attendance", "created_at")
    op.drop_column("events", "created_at")
    op.drop_constraint("uq_events_studio_code", "events", type_="unique")
    op.drop_column("events", "code")
