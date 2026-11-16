"""Add reports table for AmaApp listing moderation reports.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-16
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # 1. Create enums
    report_reason_enum = postgresql.ENUM(
        "malware",
        "scam",
        "broken",
        "inappropriate",
        "copyright",
        "other",
        name="report_reason",
        create_type=True,
    )
    report_reason_enum.create(op.get_bind(), checkfirst=True)

    report_status_enum = postgresql.ENUM(
        "pending",
        "resolved",
        "dismissed",
        name="report_status",
        create_type=True,
    )
    report_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create reports table
    op.create_table(
        "reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "app_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("apps.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "reporter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("reporter_ip_hash", sa.String(64), nullable=True),
        sa.Column(
            "reason",
            postgresql.ENUM(
                "malware",
                "scam",
                "broken",
                "inappropriate",
                "copyright",
                "other",
                name="report_reason",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "resolved",
                "dismissed",
                name="report_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column(
            "resolved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.execute("DROP TYPE IF EXISTS report_status")
    op.execute("DROP TYPE IF EXISTS report_reason")
