"""add notification logs and reminder retry fields

Revision ID: 9e3f1b7c4a21
Revises: c2f63bb9cc3f
Create Date: 2026-02-21 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9e3f1b7c4a21"
down_revision: Union[str, Sequence[str], None] = "c2f63bb9cc3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reminders", sa.Column("retry_count", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("reminders", sa.Column("max_retries", sa.Integer(), nullable=True, server_default="3"))
    op.add_column("reminders", sa.Column("last_error", sa.String(), nullable=True))
    op.add_column("reminders", sa.Column("locked_at", sa.DateTime(), nullable=True))

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("reminder_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("provider_message_id", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["reminder_id"], ["reminders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("notification_logs")
    op.drop_column("reminders", "locked_at")
    op.drop_column("reminders", "last_error")
    op.drop_column("reminders", "max_retries")
    op.drop_column("reminders", "retry_count")
