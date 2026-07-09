"""telegram_id bigint

Revision ID: 819cea87c48d
Revises: 6fc502a220d5
Create Date: 2026-07-09 20:05:13.227581
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '819cea87c48d'
down_revision: str | None = '6fc502a220d5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'users',
        'telegram_id',
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'users',
        'telegram_id',
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
