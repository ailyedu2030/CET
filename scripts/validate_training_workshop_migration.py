#!/usr/bin/env python3
"""
验证训练工坊数据库迁移文件的完整性 - 需求15
检查迁移文件与模型定义的一致性
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import MetaData, create_engine, inspect  # noqa: E402

from app.training.models.training_models import (  # noqa: E402
    TrainingParameterTemplate, TrainingTask, TrainingTaskSubmission)


def validate_migration_completeness() -> bool:
    """验证迁移文件的完整性."""
    print("🔍 开始验证训练工坊迁移文件完整性...")

    # 创建内存数据库用于测试
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()

    # 绑定模型到metadata
    TrainingParameterTemplate.metadata = metadata
    TrainingTask.metadata = metadata
    TrainingTaskSubmission.metadata = metadata

    # 创建表结构
    metadata.create_all(engine)

    # 检查表是否创建成功
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = [
        "training_parameter_templates",
        "training_tasks",
        "training_task_submissions",
    ]

    print("\n📋 检查表结构:")
    for table in expected_tables:
        if table in tables:
            print(f"  ✅ {table} - 存在")

            # 检查列
            columns = inspector.get_columns(table)
            print(f"     列数: {len(columns)}")

            # 检查索引
            indexes = inspector.get_indexes(table)
            print(f"     索引数: {len(indexes)}")

            # 检查外键
            foreign_keys = inspector.get_foreign_keys(table)
            print(f"     外键数: {len(foreign_keys)}")

        else:
            print(f"  ❌ {table} - 缺失")

    print("\n🔍 检查具体字段:")

    # 检查 training_parameter_templates 表
    if "training_parameter_templates" in tables:
        columns_list = inspector.get_columns("training_parameter_templates")
        column_names = [col["name"] for col in columns_list]
        expected_columns = [
            "id",
            "name",
            "description",
            "config",
            "is_default",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]

        print("  training_parameter_templates:")
        for col in expected_columns:
            if col in column_names:
                print(f"    ✅ {col}")
            else:
                print(f"    ❌ {col} - 缺失")

    # 检查 training_tasks 表
    if "training_tasks" in tables:
        columns_list = inspector.get_columns("training_tasks")
        column_names = [col["name"] for col in columns_list]
        expected_columns = [
            "id",
            "task_name",
            "task_type",
            "config",
            "status",
            "publish_time",
            "deadline",
            "class_id",
            "teacher_id",
            "template_id",
            "created_at",
            "updated_at",
        ]

        print("  training_tasks:")
        for col in expected_columns:
            if col in column_names:
                print(f"    ✅ {col}")
            else:
                print(f"    ❌ {col} - 缺失")

    # 检查 training_task_submissions 表
    if "training_task_submissions" in tables:
        columns_list = inspector.get_columns("training_task_submissions")
        column_names = [col["name"] for col in columns_list]
        expected_columns = [
            "id",
            "submission_data",
            "score",
            "completion_rate",
            "started_at",
            "completed_at",
            "task_id",
            "student_id",
            "created_at",
            "updated_at",
        ]

        print("  training_task_submissions:")
        for col in expected_columns:
            if col in column_names:
                print(f"    ✅ {col}")
            else:
                print(f"    ❌ {col} - 缺失")

    print("\n🔗 检查外键约束:")

    # 检查外键约束
    for table in expected_tables:
        if table in tables:
            foreign_keys = inspector.get_foreign_keys(table)
            print(f"  {table}:")
            for fk in foreign_keys:
                print(
                    f"    ✅ {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
                )

    print("\n📊 检查索引:")

    # 检查索引
    for table in expected_tables:
        if table in tables:
            indexes = inspector.get_indexes(table)
            print(f"  {table}:")
            for idx in indexes:
                print(f"    ✅ {idx['name']}: {idx['column_names']}")

    print("\n✅ 迁移文件验证完成!")
    return True


def check_migration_file_syntax() -> bool:
    """检查迁移文件语法."""
    print("\n🔍 检查迁移文件语法...")

    migration_file = (
        project_root
        / "alembic/versions/015_training_workshop_add_training_workshop_tables.py"
    )

    if not migration_file.exists():
        print(f"❌ 迁移文件不存在: {migration_file}")
        return False

    try:
        # 尝试编译迁移文件
        with open(migration_file, encoding="utf-8") as f:
            content = f.read()

        compile(content, str(migration_file), "exec")
        print("✅ 迁移文件语法正确")

        # 检查必要的函数
        if "def upgrade()" in content:
            print("✅ upgrade() 函数存在")
        else:
            print("❌ upgrade() 函数缺失")

        if "def downgrade()" in content:
            print("✅ downgrade() 函数存在")
        else:
            print("❌ downgrade() 函数缺失")

        # 检查revision信息
        if 'revision = "015_training_workshop"' in content:
            print("✅ revision ID 正确")
        else:
            print("❌ revision ID 不正确")

        if 'down_revision = "a494cbc08dd5"' in content:
            print("✅ down_revision 正确")
        else:
            print("❌ down_revision 不正确")

        return True

    except SyntaxError as e:
        print(f"❌ 迁移文件语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查迁移文件时出错: {e}")
        return False


def main() -> int:
    """主函数."""
    print("🚀 训练工坊数据库迁移验证工具")
    print("=" * 50)

    # 检查迁移文件语法
    syntax_ok = check_migration_file_syntax()

    # 验证迁移完整性
    if syntax_ok:
        completeness_ok = validate_migration_completeness()
    else:
        completeness_ok = False

    print("\n" + "=" * 50)
    if syntax_ok and completeness_ok:
        print("🎉 所有检查通过！迁移文件准备就绪。")
        return 0
    else:
        print("❌ 检查失败，请修复问题后重试。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
