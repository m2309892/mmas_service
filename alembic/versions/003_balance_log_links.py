"""balance log links and refund operation type

Revision ID: 003
Revises: 002
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE operationtype ADD VALUE IF NOT EXISTS 'refund'"))

    op.add_column(
        "balance_logs",
        sa.Column("attendance_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "balance_logs",
        sa.Column("aboniment_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "balance_logs",
        sa.Column("pay_log_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_balance_logs_attendance_id",
        "balance_logs",
        "attendance",
        ["attendance_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_balance_logs_aboniment_id",
        "balance_logs",
        "aboniments",
        ["aboniment_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_balance_logs_pay_log_id",
        "balance_logs",
        "pay_logs",
        ["pay_log_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_balance_logs_pay_log_id", "balance_logs", type_="foreignkey")
    op.drop_constraint("fk_balance_logs_aboniment_id", "balance_logs", type_="foreignkey")
    op.drop_constraint("fk_balance_logs_attendance_id", "balance_logs", type_="foreignkey")
    op.drop_column("balance_logs", "pay_log_id")
    op.drop_column("balance_logs", "aboniment_id")
    op.drop_column("balance_logs", "attendance_id")
    # PostgreSQL does not support removing enum values easily; leave refund in type.
