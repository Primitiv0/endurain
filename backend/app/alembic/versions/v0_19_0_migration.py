"""v0.19.0 migration

Revision ID: a1b2c3d4e5f6
Revises: 895a29b12c8c
Create Date: 2026-05-27 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "895a29b12c8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users_mfa and backfill from users."""
    op.create_table(
        "users_mfa",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
            comment="FK to users — one row per user",
        ),
        sa.Column(
            "mfa_enabled",
            sa.Boolean(),
            nullable=False,
            comment=(
                "Whether TOTP MFA is active for this user "
                "(mirrors users.mfa_enabled during dual-write)"
            ),
        ),
        sa.Column(
            "mfa_secret",
            sa.String(512),
            nullable=True,
            comment=(
                "Fernet-encrypted TOTP secret "
                "(mirrors users.mfa_secret during dual-write)"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            name="uq_users_mfa_user_id",
        ),
    )
    op.create_index(
        "ix_users_mfa_user_id",
        "users_mfa",
        ["user_id"],
        unique=False,
    )

    # Backfill: one row per existing user, copying the MFA
    # columns from the ``users`` table.  Only users that have
    # ``mfa_enabled = true`` carry a non-NULL ``mfa_secret``,
    # but we create a row for every user so that future writes
    # can do a simple UPDATE rather than an INSERT-OR-UPDATE.
    op.execute(
        sa.text(
            """
            INSERT INTO users_mfa (user_id, mfa_enabled, mfa_secret)
            SELECT id, mfa_enabled, mfa_secret
            FROM users
            """
        )
    )


def downgrade() -> None:
    """Drop users_mfa table (legacy columns untouched)."""
    op.drop_index(
        "ix_users_mfa_user_id",
        table_name="users_mfa",
    )
    op.drop_table("users_mfa")
