"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

paid_by_enum = sa.Enum(
    "balance",
    "hours_aboniment",
    "time_abonement",
    "unpaid",
    "other",
    name="paidby",
)
operation_type_enum = sa.Enum("credit", "debit", name="operationtype")
payment_status_enum = sa.Enum(
    "pending", "paid", "failed", "refunded", name="paymentstatus"
)


def upgrade() -> None:
    op.create_table(
        "studios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("short_name", sa.String(length=255), nullable=False),
        sa.Column("students_cnt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "belts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tg_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tg_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tg_id"),
    )

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("birth_date", sa.DateTime(), nullable=False),
        sa.Column("gender", sa.String(length=255), nullable=False),
        sa.Column("balance", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("mmas_id", sa.String(length=255), nullable=False),
        sa.Column("studio_id", sa.Integer(), nullable=False),
        sa.Column("belt_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["belt_id"], ["belts.id"]),
        sa.ForeignKeyConstraint(["studio_id"], ["studios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mmas_id"),
    )

    op.create_table(
        "app_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tg_id", sa.Integer(), nullable=False),
        sa.Column("mmas_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["tg_id"], ["tg_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("studio_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["studio_id"], ["studios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "aboniments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("studio_id", sa.Integer(), nullable=False),
        sa.Column("hours", sa.Integer(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["studio_id"], ["studios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "balance_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("operation_type", operation_type_enum, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pay_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("yookassa_id", sa.String(length=255), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("hours", sa.Time(), nullable=False),
        sa.Column("train_date", sa.DateTime(), nullable=False),
        sa.Column("paid_by", paid_by_enum, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("studio_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["studio_id"], ["studios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("attendance")
    op.drop_table("pay_logs")
    op.drop_table("balance_logs")
    op.drop_table("aboniments")
    op.drop_table("events")
    op.drop_table("app_accounts")
    op.drop_table("students")
    op.drop_table("tg_users")
    op.drop_table("belts")
    op.drop_table("studios")

    payment_status_enum.drop(op.get_bind(), checkfirst=True)
    operation_type_enum.drop(op.get_bind(), checkfirst=True)
    paid_by_enum.drop(op.get_bind(), checkfirst=True)
