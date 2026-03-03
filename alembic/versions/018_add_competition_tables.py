"""Add competition tables

Revision ID: 018_add_competition_tables
Revises: 017_add_class_student
Create Date: 2025-03-03 00:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "018_add_competition_tables"
down_revision = "017_add_class_student"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema - add competition tables."""
    # Create competitions table
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False, comment="竞赛标题"),
        sa.Column("description", sa.Text(), nullable=True, comment="竞赛描述"),
        sa.Column("competition_type", sa.String(length=50), nullable=False, comment="竞赛类型"),
        sa.Column("status", sa.String(length=50), nullable=False, comment="竞赛状态"),
        sa.Column("organizer_id", sa.Integer(), nullable=False, comment="组织者用户ID"),
        sa.Column("start_time", sa.DateTime(), nullable=False, comment="开始时间"),
        sa.Column("end_time", sa.DateTime(), nullable=False, comment="结束时间"),
        sa.Column("registration_deadline", sa.DateTime(), nullable=False, comment="报名截止时间"),
        sa.Column("max_participants", sa.Integer(), nullable=True, comment="最大参与人数"),
        sa.Column("current_participants", sa.Integer(), nullable=False, comment="当前参与人数"),
        sa.Column("difficulty_level", sa.String(length=50), nullable=False, comment="难度级别"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, comment="竞赛时长（分钟）"),
        sa.Column("question_count", sa.Integer(), nullable=False, comment="题目数量"),
        sa.Column("passing_score", sa.Float(), nullable=False, comment="及格分数"),
        sa.Column("reward_config", postgresql.JSON(astext_type=sa.Text()), nullable=True, comment="奖励配置"),
        sa.Column("rules", sa.Text(), nullable=True, comment="竞赛规则"),
        sa.Column("is_public", sa.Boolean(), nullable=False, comment="是否公开"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["organizer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="学习竞赛表",
    )
    op.create_index(op.f("ix_competitions_id"), "competitions", ["id"], unique=False)
    op.create_index(op.f("ix_competitions_status"), "competitions", ["status"], unique=False)
    op.create_index(op.f("ix_competitions_organizer_id"), "competitions", ["organizer_id"], unique=False)

    # Create competition_registrations table
    op.create_table(
        "competition_registrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False, comment="竞赛ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("registration_time", sa.DateTime(), nullable=False, comment="报名时间"),
        sa.Column("status", sa.String(length=50), nullable=False, comment="报名状态"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="竞赛报名表",
    )
    op.create_index(op.f("ix_competition_registrations_id"), "competition_registrations", ["id"], unique=False)
    op.create_index(op.f("ix_competition_registrations_competition_id"), "competition_registrations", ["competition_id"], unique=False)
    op.create_index(op.f("ix_competition_registrations_user_id"), "competition_registrations", ["user_id"], unique=False)

    # Create competition_sessions table
    op.create_table(
        "competition_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False, comment="竞赛ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("session_id", sa.String(length=100), nullable=False, comment="会话唯一标识"),
        sa.Column("start_time", sa.DateTime(), nullable=False, comment="开始时间"),
        sa.Column("end_time", sa.DateTime(), nullable=True, comment="结束时间"),
        sa.Column("current_question_index", sa.Integer(), nullable=False, comment="当前题目索引"),
        sa.Column("score", sa.Float(), nullable=False, comment="得分"),
        sa.Column("answers", postgresql.JSON(astext_type=sa.Text()), nullable=True, comment="答案记录"),
        sa.Column("status", sa.String(length=50), nullable=False, comment="会话状态"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="竞赛会话表",
    )
    op.create_index(op.f("ix_competition_sessions_id"), "competition_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_competition_sessions_competition_id"), "competition_sessions", ["competition_id"], unique=False)
    op.create_index(op.f("ix_competition_sessions_user_id"), "competition_sessions", ["user_id"], unique=False)

    # Create competition_results table
    op.create_table(
        "competition_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False, comment="竞赛ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("session_id", sa.String(length=100), nullable=False, comment="会话唯一标识"),
        sa.Column("final_score", sa.Float(), nullable=False, comment="最终得分"),
        sa.Column("rank", sa.Integer(), nullable=True, comment="排名"),
        sa.Column("completion_time", sa.Integer(), nullable=False, comment="完成时间（秒）"),
        sa.Column("correct_answers", sa.Integer(), nullable=False, comment="正确答案数"),
        sa.Column("total_questions", sa.Integer(), nullable=False, comment="总题数"),
        sa.Column("accuracy_rate", sa.Float(), nullable=False, comment="准确率"),
        sa.Column("reward_earned", postgresql.JSON(astext_type=sa.Text()), nullable=True, comment="获得的奖励"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="竞赛结果表",
    )
    op.create_index(op.f("ix_competition_results_id"), "competition_results", ["id"], unique=False)
    op.create_index(op.f("ix_competition_results_competition_id"), "competition_results", ["competition_id"], unique=False)
    op.create_index(op.f("ix_competition_results_user_id"), "competition_results", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema - drop competition tables."""
    op.drop_index(op.f("ix_competition_results_user_id"), table_name="competition_results")
    op.drop_index(op.f("ix_competition_results_competition_id"), table_name="competition_results")
    op.drop_index(op.f("ix_competition_results_id"), table_name="competition_results")
    op.drop_table("competition_results")

    op.drop_index(op.f("ix_competition_sessions_user_id"), table_name="competition_sessions")
    op.drop_index(op.f("ix_competition_sessions_competition_id"), table_name="competition_sessions")
    op.drop_index(op.f("ix_competition_sessions_id"), table_name="competition_sessions")
    op.drop_table("competition_sessions")

    op.drop_index(op.f("ix_competition_registrations_user_id"), table_name="competition_registrations")
    op.drop_index(op.f("ix_competition_registrations_competition_id"), table_name="competition_registrations")
    op.drop_index(op.f("ix_competition_registrations_id"), table_name="competition_registrations")
    op.drop_table("competition_registrations")

    op.drop_index(op.f("ix_competitions_organizer_id"), table_name="competitions")
    op.drop_index(op.f("ix_competitions_status"), table_name="competitions")
    op.drop_index(op.f("ix_competitions_id"), table_name="competitions")
    op.drop_table("competitions")
