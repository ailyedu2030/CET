#!/usr/bin/env python3
"""项目结构验证脚本."""

import importlib.util
import logging
import sys
from pathlib import Path


def _check_required_directories(
    project_root: Path,
    logger: logging.Logger,
) -> list[str]:
    """检查必需的目录"""
    issues = []
    required_dirs = [
        "app",
        "app/core",
        "app/shared",
        "app/ai",
        "app/analytics",
        "app/courses",
        "app/training",
        "app/users",
        "app/notifications",
        "app/resources",
        "frontend",
        "frontend/src",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "scripts",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            issues.append(f"❌ 缺少目录: {dir_path}")
        else:
            logger.info("✅ 目录存在: %s", dir_path)

    return issues


def _check_required_files(project_root: Path, logger: logging.Logger) -> list[str]:
    """检查必需的文件"""
    issues = []
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "frontend/src/App.tsx",
        "frontend/src/main.tsx",
        "docker-compose.yml",
        "requirements.txt",
        "package.json",
        "README.md",
    ]

    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            issues.append(f"❌ 缺少文件: {file_path}")
        else:
            logger.info("✅ 文件存在: %s", file_path)

    return issues


def _check_forbidden_items(project_root: Path, logger: logging.Logger) -> list[str]:
    """检查不应该存在的文件/目录"""
    issues = []
    forbidden_items = [
        "tsconfig.json",  # 应该只在frontend目录下
        "tsconfig.node.json",  # 应该只在frontend目录下
        "venv",  # 应该使用.venv
        "backend",  # 单体架构不应该有backend目录
        "services",  # 单体架构不应该有services目录
    ]

    for item in forbidden_items:
        full_path = project_root / item
        if full_path.exists():
            issues.append(f"❌ 不应该存在: {item}")
        else:
            logger.info("✅ 正确不存在: %s", item)

    return issues


def _check_module_structure(project_root: Path, logger: logging.Logger) -> list[str]:
    """检查模块结构"""
    issues = []
    modules = [
        "ai",
        "analytics",
        "courses",
        "training",
        "users",
        "notifications",
        "resources",
    ]

    for module in modules:
        module_path = project_root / "app" / module
        if module_path.exists():
            init_file = module_path / "__init__.py"
            if not init_file.exists():
                issues.append(f"❌ 模块缺少__init__.py: app/{module}")
            else:
                logger.info("✅ 模块结构正确: app/%s", module)

    return issues


def check_directory_structure() -> bool:
    """检查项目目录结构是否符合设计规范."""
    logger = logging.getLogger(__name__)
    project_root = Path(__file__).parent.parent

    # 收集所有问题
    all_issues = []

    # 检查各个部分
    all_issues.extend(_check_required_directories(project_root, logger))
    all_issues.extend(_check_required_files(project_root, logger))
    all_issues.extend(_check_forbidden_items(project_root, logger))
    all_issues.extend(_check_module_structure(project_root, logger))

    # 输出结果
    if all_issues:
        logger.info("\n🚨 发现以下问题:")
        for issue in all_issues:
            logger.info("  %s", issue)
        return False

    logger.info("\n🎉 项目结构验证通过!")
    return True


def check_python_imports() -> bool:
    """检查Python导入是否正确."""
    logger = logging.getLogger(__name__)

    try:
        # 检查核心模块导入
        sys.path.insert(0, str(Path(__file__).parent.parent))

        config_spec = importlib.util.find_spec("app.core.config")
        if config_spec is None:
            logger.error("❌ 无法找到app.core.config模块")
            return False

        database_spec = importlib.util.find_spec("app.core.database")
        if database_spec is None:
            logger.error("❌ 无法找到app.core.database模块")
            return False

        logger.info("✅ 配置模块导入成功")
        logger.info("✅ 数据库模块导入成功")

    except ImportError:
        logger.exception("❌ 导入错误")
        return False
    else:
        return True


def main() -> None:
    """主函数."""
    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("🔍 开始验证项目结构...")
    logger.info("=" * 50)

    structure_ok = check_directory_structure()

    separator = "=" * 50
    logger.info("\n%s", separator)
    logger.info("🔍 检查Python导入...")

    imports_ok = check_python_imports()

    logger.info("\n%s", separator)

    if structure_ok and imports_ok:
        logger.info("🎉 项目结构完全符合设计规范!")
        sys.exit(0)
    else:
        logger.info("🚨 项目结构存在问题, 请修正后重新验证")
        sys.exit(1)


if __name__ == "__main__":
    main()
