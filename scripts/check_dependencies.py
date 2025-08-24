#!/usr/bin/env python3
"""
依赖配置检查脚本 - 基于设计文档v1.0
检查前后端依赖是否正确配置和安装，符合零缺陷交付标准
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class DependencyChecker:
    """依赖检查器 - 零缺陷标准"""

    def __init__(self) -> None:
        self.project_root = Path.cwd()
        self.missing_python_packages: set[str] = set()
        self.missing_node_packages: set[str] = set()
        self.design_requirements = self._load_design_requirements()

    def _load_design_requirements(self) -> dict[str, dict[str, list[str]]]:
        """加载设计文档要求的依赖"""
        return {
            "python": {
                "core_framework": [
                    "fastapi",
                    "uvicorn",
                    "pydantic",
                    "pydantic-settings",
                ],
                "database": ["sqlalchemy", "alembic", "asyncpg", "psycopg2-binary"],
                "ai_services": ["openai", "httpx", "aiohttp", "anthropic"],
                "vector_db": ["pymilvus", "sentence-transformers"],
                "cache_queue": ["redis", "celery", "kombu"],
                "object_storage": ["minio"],
                "auth_security": ["python-jose", "passlib", "cryptography"],
                "document_processing": [
                    "pypdf2",
                    "python-docx",
                    "openpyxl",
                    "pandas",
                    "numpy",
                ],
                "monitoring": [
                    "prometheus-client",
                    "prometheus-fastapi-instrumentator",
                ],
                "quality_tools": [
                    "ruff",
                    "mypy",
                    "pytest",
                    "pytest-asyncio",
                    "pytest-cov",
                    "pytest-mock",
                    "pytest-benchmark",
                    "black",
                    "isort",
                    "bandit",
                    "pip-audit",
                    "radon",
                ],
                "utilities": [
                    "python-dateutil",
                    "pytz",
                    "loguru",
                    "structlog",
                    "pillow",
                ],
            },
            "node": {
                "core_framework": ["react", "react-dom", "typescript", "vite"],
                "ui_components": [
                    "@mantine/core",
                    "@mantine/hooks",
                    "@mantine/form",
                    "@mantine/notifications",
                    "@mantine/modals",
                    "@mantine/charts",
                ],
                "state_management": ["zustand", "@tanstack/react-query"],
                "routing": ["react-router-dom"],
                "http_client": ["axios"],
                "forms": ["react-hook-form", "@hookform/resolvers", "zod"],
                "icons": ["@tabler/icons-react"],
                "utilities": ["dayjs", "lodash", "uuid", "js-cookie"],
                "realtime": ["socket.io-client"],
                "testing": [
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event",
                    "vitest",
                    "@vitest/ui",
                    "@vitest/coverage-v8",
                    "playwright",
                    "@playwright/test",
                ],
                "dev_tools": [
                    "@typescript-eslint/eslint-plugin",
                    "@typescript-eslint/parser",
                    "eslint",
                    "eslint-plugin-react-hooks",
                    "eslint-plugin-import",
                    "eslint-plugin-jsx-a11y",
                ],
            },
        }

    def check_config_files(self) -> dict[str, bool]:
        """检查配置文件是否存在且符合设计文档要求"""
        config_files = {
            "requirements.txt": self.project_root / "requirements.txt",
            "package.json": self.project_root / "package.json",
            "pyproject.toml": self.project_root / "pyproject.toml",
            "frontend/tsconfig.json": self.project_root / "frontend" / "tsconfig.json",
            "vite.config.ts": self.project_root / "vite.config.ts",
            ".eslintrc.cjs": self.project_root / ".eslintrc.cjs",
            "docker-compose.yml": self.project_root / "docker-compose.yml",
        }

        results = {}
        for name, path in config_files.items():
            results[name] = path.exists()

        return results

    def check_python_dependencies(self) -> tuple[dict[str, bool], dict[str, list[str]]]:
        """检查Python依赖是否安装且符合设计文档要求"""
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            return {}, {}

        # 读取requirements.txt
        with open(requirements_file, encoding="utf-8") as f:
            lines = f.readlines()

        # 提取包名
        installed_packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # 提取包名（去掉版本号和额外依赖）
                package_name = line.split("==")[0].split(">=")[0].split("[")[0]
                installed_packages.append(package_name)

        # 检查每个包是否安装
        results = {}
        for package in installed_packages:
            try:
                # 特殊处理一些包名映射
                import_name = self._get_import_name(package)
                subprocess.run(
                    [sys.executable, "-c", f"import {import_name}"],
                    check=True,
                    capture_output=True,
                )
                results[package] = True
            except subprocess.CalledProcessError:
                results[package] = False
                self.missing_python_packages.add(package)

        # 检查设计文档要求的关键依赖
        missing_categories = {}
        for category, packages in self.design_requirements["python"].items():
            missing_in_category = []
            for package in packages:
                if package not in installed_packages:
                    missing_in_category.append(package)
            if missing_in_category:
                missing_categories[category] = missing_in_category

        return results, missing_categories

    def check_node_dependencies(self) -> tuple[dict[str, Any], dict[str, list[str]]]:
        """检查Node.js依赖是否安装且符合设计文档要求"""
        package_json = self.project_root / "package.json"
        if not package_json.exists():
            return {}, {}

        # 读取package.json
        with open(package_json, encoding="utf-8") as f:
            package_data = json.load(f)

        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})
        all_deps = {**dependencies, **dev_dependencies}

        # 检查node_modules是否存在
        node_modules = self.project_root / "node_modules"
        node_modules_exists = node_modules.exists()

        if not node_modules_exists:
            for package in all_deps:
                self.missing_node_packages.add(package)

        # 检查设计文档要求的关键依赖
        missing_categories = {}
        for category, packages in self.design_requirements["node"].items():
            missing_in_category = []
            for package in packages:
                if package not in all_deps:
                    missing_in_category.append(package)
            if missing_in_category:
                missing_categories[category] = missing_in_category

        return {
            "total_packages": len(all_deps),
            "node_modules_exists": node_modules_exists,
            "packages": all_deps,
        }, missing_categories

    def check_version_compatibility(self) -> dict[str, bool]:
        """检查版本兼容性"""
        compatibility = {}

        # 检查Python版本 (要求3.11+)
        python_version = sys.version_info
        compatibility["python_version"] = python_version >= (3, 11)

        # 检查Node.js版本 (要求18+)
        try:
            result = subprocess.run(
                ["node", "--version"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                node_version = result.stdout.strip().lstrip("v")
                major_version = int(node_version.split(".")[0])
                compatibility["node_version"] = major_version >= 18
            else:
                compatibility["node_version"] = False
        except (subprocess.CalledProcessError, FileNotFoundError):
            compatibility["node_version"] = False

        return compatibility

    def _get_import_name(self, package_name: str) -> str:
        """获取包的导入名称"""
        import_mapping = {
            "python-jose": "jose",
            "python-dateutil": "dateutil",
            "python-multipart": "multipart",
            "python-dotenv": "dotenv",
            "pydantic-settings": "pydantic_settings",
            "pydantic-extra-types": "pydantic_extra_types",
            "prometheus-client": "prometheus_client",
            "prometheus-fastapi-instrumentator": "prometheus_fastapi_instrumentator",
            "pip-audit": "pip_audit",
            "sentence-transformers": "sentence_transformers",
        }
        return import_mapping.get(package_name, package_name.replace("-", "_"))

    def print_results(
        self,
        config_results: dict[str, bool],
        python_results: tuple[dict[str, bool], dict[str, list[str]]],
        node_results: tuple[dict[str, Any], dict[str, list[str]]],
        compatibility: dict[str, bool],
    ) -> bool:
        """打印检查结果 - 详细报告"""
        print("🔍 英语四级学习系统依赖配置检查 (设计文档v1.0)")
        print("=" * 80)

        python_installed, python_missing_categories = python_results
        node_installed, node_missing_categories = node_results

        # 版本兼容性检查
        print("\n🔧 版本兼容性检查...")
        print("=" * 60)
        python_ok = compatibility.get("python_version", False)
        node_ok = compatibility.get("node_version", False)
        print(f"🐍 Python版本: {'✅ >=3.11' if python_ok else '❌ <3.11 (需要升级)'}")
        print(f"📦 Node.js版本: {'✅ >=18' if node_ok else '❌ <18 (需要升级)'}")

        # 配置文件检查
        print("\n⚙️ 配置文件检查...")
        print("=" * 60)
        for name, exists in config_results.items():
            status = "✅" if exists else "❌"
            desc = self._get_config_description(name)
            print(f"{status} {desc}: {name}")

        # Python依赖检查
        print("\n🐍 Python后端依赖检查...")
        print("=" * 60)
        if python_installed:
            installed_count = sum(
                1 for installed in python_installed.values() if installed
            )
            total_count = len(python_installed)
            print(f"📊 已安装: {installed_count}/{total_count} 个包")

            if self.missing_python_packages:
                print("❌ 未安装的包:")
                for package in sorted(self.missing_python_packages):
                    print(f"   - {package}")
            else:
                print("✅ 所有配置的包已安装")

            if python_missing_categories:
                print("\n⚠️ 设计文档要求但未配置的依赖:")
                for category, packages in python_missing_categories.items():
                    print(f"   {category}: {', '.join(packages)}")
        else:
            print("❌ 无法读取requirements.txt")

        # Node.js依赖检查
        print("\n📦 Node.js前端依赖检查...")
        print("=" * 60)
        if node_installed:
            print(f"📋 配置的依赖数量: {node_installed['total_packages']}")
            if node_installed["node_modules_exists"]:
                print("✅ node_modules 目录存在")
            else:
                print("❌ node_modules 目录不存在，依赖未安装")

            if node_missing_categories:
                print("\n⚠️ 设计文档要求但未配置的依赖:")
                for category, packages in node_missing_categories.items():
                    print(f"   {category}: {', '.join(packages)}")
        else:
            print("❌ 无法读取package.json")

        # 总结
        print("\n" + "=" * 80)
        print("📊 依赖检查总结")
        print("=" * 80)

        config_ok = all(config_results.values())
        python_deps_ok = len(self.missing_python_packages) == 0
        node_deps_ok = len(self.missing_node_packages) == 0
        design_compliant = (
            len(python_missing_categories) == 0 and len(node_missing_categories) == 0
        )

        print(
            f"🔧 版本兼容性: {'✅ 符合要求' if python_ok and node_ok else '❌ 需要升级'}",
        )
        print(f"⚙️ 配置文件: {'✅ 完整' if config_ok else '❌ 缺失'}")
        print(f"🐍 Python依赖: {'✅ 已安装' if python_deps_ok else '❌ 未安装'}")
        print(f"📦 Node.js依赖: {'✅ 已安装' if node_deps_ok else '❌ 未安装'}")
        print(
            f"📋 设计文档符合性: {'✅ 完全符合' if design_compliant else '⚠️ 部分缺失'}",
        )

        # 安装命令
        if not python_deps_ok or not node_deps_ok:
            print("\n🛠️ 依赖安装命令...")
            print("=" * 60)
            if not python_deps_ok:
                print("# Python后端依赖安装:")
                print("pip install -r requirements.txt")
                print("# 或使用虚拟环境:")
                print("python -m venv .venv")
                print("source .venv/bin/activate  # Linux/Mac")
                print("# .venv\\Scripts\\activate  # Windows")
                print("pip install -r requirements.txt")

            if not node_deps_ok:
                print("\n# Node.js前端依赖安装:")
                print("npm install")
                print("# 或者使用yarn:")
                print("yarn install")

            print("\n# 验证安装:")
            print("python3 scripts/check_dependencies.py")

        # Docker部署检查
        if config_results.get("docker-compose.yml", False):
            print("\n🐳 Docker部署选项...")
            print("=" * 60)
            print("# 使用Docker一键部署 (推荐):")
            print("docker-compose up -d")
            print("# 这将自动安装所有依赖并启动服务")

        return python_ok and node_ok and config_ok and python_deps_ok and node_deps_ok

    def _get_config_description(self, filename: str) -> str:
        """获取配置文件描述"""
        descriptions = {
            "requirements.txt": "Python依赖配置",
            "package.json": "Node.js依赖配置",
            "pyproject.toml": "Python项目配置",
            "frontend/tsconfig.json": "TypeScript配置",
            "vite.config.ts": "Vite构建配置",
            ".eslintrc.cjs": "ESLint配置",
            "docker-compose.yml": "Docker编排配置",
        }
        return descriptions.get(filename, "配置文件")


def main() -> None:
    """主函数"""
    checker = DependencyChecker()

    # 执行检查
    config_results = checker.check_config_files()
    python_results = checker.check_python_dependencies()
    node_results = checker.check_node_dependencies()
    compatibility = checker.check_version_compatibility()

    # 打印结果
    success = checker.print_results(
        config_results,
        python_results,
        node_results,
        compatibility,
    )

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
