"""Add user security fields: password_history, password_changed_at, failed_login_attempts, locked_until

Revision ID: add_user_security_fields
Revises: a494cbc08dd5
Create Date: 2026-02-27

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "add_user_security_fields"
down_revision: str | Sequence[str] | None = "a494cbc08dd5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add security fields to users table."""
    # Add password_changed_at
    op.add_column(
        "users",
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="密码最后修改时间",
        ),
    )

    # Add failed_login_attempts
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="连续登录失败次数",
        ),
    )

    # Add locked_until
    op.add_column(
        "users",
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="账户锁定截止时间",
        ),
    )

    # Add password_history (JSON array)
    op.add_column(
        "users",
        sa.Column(
            "password_history",
            sa.JSON(),
            nullable=False,
            server_default="[]",
            comment="密码历史（存储hash）",
        ),
    )


def downgrade() -> None:
    """Remove security fields from users table."""
    op.drop_column("users", "password_history")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "password_changed_at")
