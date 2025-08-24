"""Add training workshop tables - 需求15实现

Revision ID: 015_training_workshop
Revises: 014_lesson_plan_builder
Create Date: 2024-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "015_training_workshop"
down_revision = "a494cbc08dd5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库架构 - 添加训练工坊相关表."""

    # 创建训练参数模板表
    op.create_table(
        "training_parameter_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="训练参数模板表 - 需求15验收标准2",
    )

    # 创建索引
    op.create_index(
        "ix_training_parameter_templates_name", "training_parameter_templates", ["name"]
    )
    op.create_index(
        "ix_training_parameter_templates_created_by",
        "training_parameter_templates",
        ["created_by"],
    )
    op.create_index(
        "ix_training_parameter_templates_is_default",
        "training_parameter_templates",
        ["is_default"],
    )
    op.create_index(
        "ix_training_parameter_templates_is_active",
        "training_parameter_templates",
        ["is_active"],
    )

    # 创建复合索引用于查询优化
    op.create_index(
        "ix_training_parameter_templates_created_by_active",
        "training_parameter_templates",
        ["created_by", "is_active"],
    )

    # 创建训练任务表
    op.create_table(
        "training_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(length=200), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, default="draft"),
        sa.Column("publish_time", sa.DateTime(), nullable=True),
        sa.Column("deadline", sa.DateTime(), nullable=True),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["template_id"], ["training_parameter_templates.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="训练任务表 - 需求15验收标准4",
    )

    # 创建索引
    op.create_index("ix_training_tasks_task_name", "training_tasks", ["task_name"])
    op.create_index("ix_training_tasks_task_type", "training_tasks", ["task_type"])
    op.create_index("ix_training_tasks_status", "training_tasks", ["status"])
    op.create_index("ix_training_tasks_class_id", "training_tasks", ["class_id"])
    op.create_index("ix_training_tasks_teacher_id", "training_tasks", ["teacher_id"])
    op.create_index("ix_training_tasks_template_id", "training_tasks", ["template_id"])
    op.create_index("ix_training_tasks_publish_time", "training_tasks", ["publish_time"])
    op.create_index("ix_training_tasks_deadline", "training_tasks", ["deadline"])

    # 创建复合索引用于查询优化
    op.create_index("ix_training_tasks_teacher_class", "training_tasks", ["teacher_id", "class_id"])
    op.create_index(
        "ix_training_tasks_status_publish_time",
        "training_tasks",
        ["status", "publish_time"],
    )

    # 创建训练任务提交记录表
    op.create_table(
        "training_task_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("completion_rate", sa.Float(), nullable=False, default=0.0),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["training_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "completion_rate >= 0.0 AND completion_rate <= 1.0",
            name="ck_completion_rate_range",
        ),
        sa.CheckConstraint("score IS NULL OR score >= 0.0", name="ck_score_non_negative"),
        comment="训练任务提交记录表 - 需求15验收标准5",
    )

    # 创建索引
    op.create_index(
        "ix_training_task_submissions_task_id", "training_task_submissions", ["task_id"]
    )
    op.create_index(
        "ix_training_task_submissions_student_id",
        "training_task_submissions",
        ["student_id"],
    )
    op.create_index(
        "ix_training_task_submissions_completed_at",
        "training_task_submissions",
        ["completed_at"],
    )

    # 创建复合索引用于查询优化
    op.create_index(
        "ix_training_task_submissions_task_student",
        "training_task_submissions",
        ["task_id", "student_id"],
        unique=True,
    )


def downgrade() -> None:
    """降级数据库架构 - 删除训练工坊相关表."""

    # 删除索引
    op.drop_index(
        "ix_training_task_submissions_task_student",
        table_name="training_task_submissions",
    )
    op.drop_index(
        "ix_training_task_submissions_completed_at",
        table_name="training_task_submissions",
    )
    op.drop_index(
        "ix_training_task_submissions_student_id",
        table_name="training_task_submissions",
    )
    op.drop_index("ix_training_task_submissions_task_id", table_name="training_task_submissions")

    op.drop_index("ix_training_tasks_status_publish_time", table_name="training_tasks")
    op.drop_index("ix_training_tasks_teacher_class", table_name="training_tasks")
    op.drop_index("ix_training_tasks_deadline", table_name="training_tasks")
    op.drop_index("ix_training_tasks_publish_time", table_name="training_tasks")
    op.drop_index("ix_training_tasks_template_id", table_name="training_tasks")
    op.drop_index("ix_training_tasks_teacher_id", table_name="training_tasks")
    op.drop_index("ix_training_tasks_class_id", table_name="training_tasks")
    op.drop_index("ix_training_tasks_status", table_name="training_tasks")
    op.drop_index("ix_training_tasks_task_type", table_name="training_tasks")
    op.drop_index("ix_training_tasks_task_name", table_name="training_tasks")

    op.drop_index(
        "ix_training_parameter_templates_created_by_active",
        table_name="training_parameter_templates",
    )
    op.drop_index(
        "ix_training_parameter_templates_is_active",
        table_name="training_parameter_templates",
    )
    op.drop_index(
        "ix_training_parameter_templates_is_default",
        table_name="training_parameter_templates",
    )
    op.drop_index(
        "ix_training_parameter_templates_created_by",
        table_name="training_parameter_templates",
    )
    op.drop_index(
        "ix_training_parameter_templates_name",
        table_name="training_parameter_templates",
    )

    # 删除表
    op.drop_table("training_task_submissions")
    op.drop_table("training_tasks")
    op.drop_table("training_parameter_templates")
