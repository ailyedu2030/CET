"""Add intelligent training loop model for requirement 21

Revision ID: 016_intelligent_training_loop
Revises: 015_training_workshop
Create Date: 2024-08-24 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "016_intelligent_training_loop"
down_revision = "015_training_workshop"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add intelligent training loop table."""
    # Create intelligent_training_loops table
    op.create_table(
        "intelligent_training_loops",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"
        ),
        sa.Column("student_id", sa.Integer(), nullable=False, comment="学生ID"),
        sa.Column(
            "training_type",
            postgresql.ENUM(
                "VOCABULARY",
                "LISTENING",
                "READING",
                "WRITING",
                "TRANSLATION",
                "GRAMMAR",
                "COMPREHENSIVE",
                name="trainingtype",
                create_type=False,
            ),
            nullable=False,
            comment="训练类型",
        ),
        sa.Column(
            "execution_time",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="执行时间",
        ),
        sa.Column(
            "next_execution_time",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="下次执行时间",
        ),
        sa.Column(
            "data_collection_result", sa.JSON(), nullable=False, comment="数据采集结果"
        ),
        sa.Column(
            "ai_analysis_result", sa.JSON(), nullable=False, comment="AI分析结果"
        ),
        sa.Column(
            "strategy_adjustment_result",
            sa.JSON(),
            nullable=False,
            comment="策略调整结果",
        ),
        sa.Column(
            "effect_verification_result",
            sa.JSON(),
            nullable=False,
            comment="效果验证结果",
        ),
        sa.Column("loop_success", sa.Boolean(), nullable=False, comment="闭环是否成功"),
        sa.Column(
            "ai_analysis_accuracy", sa.Float(), nullable=False, comment="AI分析准确率"
        ),
        sa.Column("improvement_rate", sa.Float(), nullable=False, comment="改进率"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=True, comment="更新时间"
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        "ix_intelligent_training_loops_student_id",
        "intelligent_training_loops",
        ["student_id"],
    )
    op.create_index(
        "ix_intelligent_training_loops_training_type",
        "intelligent_training_loops",
        ["training_type"],
    )


def downgrade() -> None:
    """Remove intelligent training loop table."""
    op.drop_index(
        "ix_intelligent_training_loops_training_type",
        table_name="intelligent_training_loops",
    )
    op.drop_index(
        "ix_intelligent_training_loops_student_id",
        table_name="intelligent_training_loops",
    )
    op.drop_table("intelligent_training_loops")
