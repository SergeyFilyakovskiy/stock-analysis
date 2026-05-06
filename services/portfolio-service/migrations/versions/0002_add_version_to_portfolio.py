"""add version to portfolio (already in 0001, guard migration)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # version уже создан в 0001; эта миграция — явный чекпоинт
    # для команды, что поле намеренно добавлено для optimistic locking
    pass


def downgrade() -> None:
    pass