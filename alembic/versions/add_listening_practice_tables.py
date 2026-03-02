"""Add listening practice tables: dictation, speaking, pronunciation

Revision ID: add_listening_practice_tables
Revises: a494cbc08dd5
Create Date: 2026-02-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision: str = "add_listening_practice_tables"
down_revision: str | Sequence[str] | None = "017_add_class_student"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Dictation Exercises
    op.create_table(
        "dictation_exercises",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False, primary_key=True
        ),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column(
            "user_answers",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("total_blanks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["exercise_id"], ["listening_exercises.id"]),
    )

    # Speaking Practices
    op.create_table(
        "speaking_practices",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False, primary_key=True
        ),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("audio_file_id", sa.Integer(), nullable=True),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("pronunciation_score", sa.Float(), nullable=True),
        sa.Column("fluency_score", sa.Float(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column(
            "feedback",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["exercise_id"], ["listening_exercises.id"]),
        sa.ForeignKeyConstraint(["audio_file_id"], ["listening_audio_files.id"]),
    )

    # Pronunciation Practices
    op.create_table(
        "pronunciation_practices",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False, primary_key=True
        ),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("target_text", sa.String(255), nullable=False),
        sa.Column("audio_file_id", sa.Integer(), nullable=True),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column(
            "phoneme_scores",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["exercise_id"], ["listening_exercises.id"]),
        sa.ForeignKeyConstraint(["audio_file_id"], ["listening_audio_files.id"]),
    )


def downgrade() -> None:
    op.drop_table("pronunciation_practices")
    op.drop_table("speaking_practices")
    op.drop_table("dictation_exercises")
