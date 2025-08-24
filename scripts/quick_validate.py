#!/usr/bin/env python3
"""快速项目结构验证脚本."""

import sys
from pathlib import Path


def main() -> bool:
    """主函数."""

    print("🔍 快速验证项目结构...")
    print("=" * 50)

    project_root = Path(__file__).parent.parent
    issues = []

    # 检查关键文件
    key_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/config.py",
        "app/core/database.py",
        "frontend/src/App.tsx",
        "docker-compose.yml",
        "requirements.txt",
    ]

    for file_path in key_files:
        full_path = project_root / file_path
        if not full_path.exists():
            issues.append(f"❌ 缺少关键文件: {file_path}")
        else:
            print(f"✅ 关键文件存在: {file_path}")

    # 检查不应该存在的文件
    forbidden_items = [
        "tsconfig.json",  # 应该只在frontend目录下
        "venv",  # 应该使用.venv
        "backend",  # 单体架构不应该有
        "services",  # 单体架构不应该有
    ]

    for item in forbidden_items:
        full_path = project_root / item
        if full_path.exists():
            issues.append(f"❌ 不应该存在: {item}")
        else:
            print(f"✅ 正确不存在: {item}")

    # 检查Python导入
    try:
        sys.path.insert(0, str(project_root))
        from app.core.config import settings

        print(f"✅ 配置导入成功: {settings.PROJECT_NAME}")
    except ImportError as e:
        issues.append(f"❌ 配置导入失败: {e}")

    print("\n" + "=" * 50)

    if issues:
        print("🚨 发现问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    print("🎉 项目结构验证通过!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
