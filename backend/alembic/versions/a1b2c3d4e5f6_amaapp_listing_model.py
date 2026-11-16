"""AmaApp listing model: listing_type, is_unreviewed, debug build fields, web_app_listings table.

Revision ID: a1b2c3d4e5f6
Revises: (previous head — set by alembic merge-heads if needed)
Create Date: 2026-11-16

What this migration does
------------------------
1. Adds the ``listing_type`` enum + column to ``apps`` (default ``apk``).
2. Adds ``is_unreviewed`` boolean column to ``apps`` (default ``true``).
3. Adds three columns to ``apks``: ``is_debug_build``, ``vibe_tool``, ``changelog``.
4. Creates the new ``web_app_listings`` table for web-app-specific metadata.

All new columns have sensible defaults so the migration is backward-compatible
with existing data: every existing app becomes an ``apk`` listing and is marked
``is_unreviewed = false`` (they were already reviewed before this migration ran).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None  # set to current head when applying
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # 1. listing_type enum + column on apps
    listing_type_enum = postgresql.ENUM(
        "apk", "web_app", name="listing_type", create_type=True
    )
    listing_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "apps",
        sa.Column(
            "listing_type",
            sa.Enum("apk", "web_app", name="listing_type"),
            nullable=False,
            server_default="apk",
        ),
    )
    op.create_index("ix_apps_listing_type", "apps", ["listing_type"])

    # 2. is_unreviewed on apps
    # Existing rows pre-date this migration and were already moderated,
    # so we backfill them as reviewed (False).
    op.add_column(
        "apps",
        sa.Column(
            "is_unreviewed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index("ix_apps_is_unreviewed", "apps", ["is_unreviewed"])

    # 3. APK debug-build columns
    op.add_column(
        "apks",
        sa.Column(
            "is_debug_build",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index("ix_apks_is_debug_build", "apks", ["is_debug_build"])
    op.add_column("apks", sa.Column("vibe_tool", sa.String(255), nullable=True))
    op.add_column("apks", sa.Column("changelog", sa.Text(), nullable=True))

    # 4. web_app_listings table
    op.create_table(
        "web_app_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("app_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("screenshot_keys", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("tech_stack", sa.String(255), nullable=True),
        sa.Column("url_check_passed", sa.Boolean(), nullable=True),
        sa.UniqueConstraint("app_id", name="uq_web_app_listing_app"),
    )


def downgrade() -> None:
    op.drop_table("web_app_listings")

    op.drop_index("ix_apks_is_debug_build", table_name="apks")
    op.drop_column("apks", "changelog")
    op.drop_column("apks", "vibe_tool")
    op.drop_column("apks", "is_debug_build")

    op.drop_index("ix_apps_is_unreviewed", table_name="apps")
    op.drop_column("apps", "is_unreviewed")

    op.drop_index("ix_apps_listing_type", table_name="apps")
    op.drop_column("apps", "listing_type")

    sa.Enum(name="listing_type").drop(op.get_bind(), checkfirst=True)
