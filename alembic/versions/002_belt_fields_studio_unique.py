"""belt fields and studio short_name unique

Revision ID: 002
Revises: 001
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "belts",
        sa.Column("code", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "belts",
        sa.Column("style", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "belts",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute(
        sa.text(
            "UPDATE belts SET code = LOWER(REPLACE(color, ' ', '-')) "
            "WHERE code IS NULL"
        )
    )
    op.alter_column("belts", "code", nullable=False)
    op.create_unique_constraint("uq_belts_code", "belts", ["code"])

    op.create_unique_constraint("uq_studios_short_name", "studios", ["short_name"])


def downgrade() -> None:
    op.drop_constraint("uq_studios_short_name", "studios", type_="unique")
    op.drop_constraint("uq_belts_code", "belts", type_="unique")
    op.drop_column("belts", "sort_order")
    op.drop_column("belts", "style")
    op.drop_column("belts", "code")
