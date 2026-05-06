"""add outbox_events table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("routing_key", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_events_created_at", "outbox_events", ["created_at"])
    # Partial index — только непосланные события, для быстрого polling
    op.execute(
        "CREATE INDEX ix_outbox_events_pending ON outbox_events (created_at) "
        "WHERE sent_at IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_pending", "outbox_events")
    op.drop_index("ix_outbox_events_created_at", "outbox_events")
    op.drop_table("outbox_events")