"""Add VirusTotal scan metadata columns to apks table.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-16
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column("apks", sa.Column("vt_status", sa.String(32), nullable=True))
    op.add_column("apks", sa.Column("vt_positives", sa.Integer(), nullable=True))
    op.add_column("apks", sa.Column("vt_total", sa.Integer(), nullable=True))
    op.add_column("apks", sa.Column("vt_permalink", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("apks", "vt_permalink")
    op.drop_column("apks", "vt_total")
    op.drop_column("apks", "vt_positives")
    op.drop_column("apks", "vt_status")
