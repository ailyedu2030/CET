#!/usr/bin/env python3
"""
严格验证脚本 - 零缺陷交付标准
验证所有配置是否完全符合设计文档v1.0要求
"""

import json
import logging
import re
import sys
from pathlib import Path


class StrictValidator:
    """严格验证器 - 零缺陷标准"""

    def __init__(self) -> None:
        self.project_root = Path.cwd()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.logger = logging.getLogger(__name__)

    def validate_all(self) -> bool:
        """执行所有验证"""
        # 配置日志
        logging.basicConfig(level=logging.INFO, format="%(message)s")

        self.logger.info("🔍 严格验证 - 零缺陷交付标准")
        self.logger.info("=" * 60)

        # 1. 验证项目结构
        self.validate_project_structure()

        # 2. 验证Python配置
        self.validate_python_config()

        # 3. 验证TypeScript配置
        self.validate_typescript_config()

        # 4. 验证ESLint配置
        self.validate_eslint_config()

        # 5. 验证Docker配置
        self.validate_docker_config()

        # 6. 验证依赖版本
        self.validate_dependency_versions()

        # 7. 验证质量工具配置
        self.validate_quality_tools()

        # 打印结果
        self.print_results()

        return len(self.errors) == 0

    def validate_project_structure(self) -> None:
        """验证项目结构符合设计文档"""
        self.logger.info("\n📁 验证项目结构...")

        required_structure = {
            "app/": "后端单体应用目录",
            "app/main.py": "FastAPI应用入口",
            "app/core/": "核心配置目录",
            "app/users/": "用户管理模块",
            "app/courses/": "课程管理模块",
            "app/training/": "训练系统模块",
            "app/ai/": "AI集成模块",
            "app/notifications/": "通知系统模块",
            "app/analytics/": "数据分析模块",
            "app/resources/": "资源库模块",
            "app/shared/": "共享组件",
            "frontend/": "前端应用目录",
            "frontend/src/": "前端源码目录",
            "tests/": "测试目录",
            "scripts/": "脚本目录",
            "requirements.txt": "Python依赖配置",
            "package.json": "Node.js依赖配置",
            "pyproject.toml": "Python项目配置",
            "docker-compose.yml": "Docker编排配置",
        }

        for path, description in required_structure.items():
            full_path = self.project_root / path
            if not full_path.exists():
                self.errors.append(f"缺少{description}: {path}")
            else:
                self.logger.info("✅ %s: %s", description, path)

    def validate_python_config(self) -> None:
        """验证Python配置符合设计文档"""
        self.logger.info("\n🐍 验证Python配置...")

        # 检查pyproject.toml
        pyproject_file = self.project_root / "pyproject.toml"
        if not pyproject_file.exists():
            self.errors.append("缺少pyproject.toml配置文件")
            return

        content = pyproject_file.read_text(encoding="utf-8")

        # 验证Ruff配置
        if 'target-version = "py311"' not in content:
            self.errors.append("pyproject.toml中Ruff目标版本不是py311")
        else:
            self.logger.info("✅ Ruff目标版本: py311")

        # 验证严格的选择规则
        required_ruff_rules = [
            '"E"',
            '"W"',
            '"F"',  # pycodestyle, pyflakes
            '"I"',  # isort
            '"N"',  # pep8-naming
            '"UP"',  # pyupgrade
            '"ANN"',  # flake8-annotations
            '"S"',  # flake8-bandit
            '"B"',  # flake8-bugbear
        ]

        for rule in required_ruff_rules:
            if rule not in content:
                self.errors.append(f"pyproject.toml中缺少Ruff规则: {rule}")
            else:
                self.logger.info("✅ Ruff规则: %s", rule)

        # 验证mypy严格模式
        if "strict = true" not in content:
            self.errors.append("pyproject.toml中mypy未启用严格模式")
        else:
            self.logger.info("✅ mypy严格模式已启用")

    def validate_typescript_config(self) -> None:
        """验证TypeScript配置符合设计文档"""
        self.logger.info("\n📘 验证TypeScript配置...")

        tsconfig_file = self.project_root / "frontend" / "tsconfig.json"
        if not tsconfig_file.exists():
            self.errors.append("缺少frontend/tsconfig.json配置文件")
            return

        try:
            content = tsconfig_file.read_text(encoding="utf-8")
            config = json.loads(content)
        except json.JSONDecodeError:
            self.errors.append("frontend/tsconfig.json格式错误")
            return

        compiler_options = config.get("compilerOptions", {})

        # 验证严格类型检查
        strict_options = {
            "strict": True,
            "noImplicitAny": True,
            "strictNullChecks": True,
            "strictFunctionTypes": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noImplicitReturns": True,
            "noFallthroughCasesInSwitch": True,
        }

        for option, expected in strict_options.items():
            actual = compiler_options.get(option)
            if actual != expected:
                self.errors.append(
                    f"tsconfig.json中{option}应为{expected}, 实际为{actual}",
                )
            else:
                self.logger.info("✅ TypeScript严格选项: %s", option)

        # 验证目标版本
        target = compiler_options.get("target")
        if target not in ["ES2022", "ES2020"]:
            self.warnings.append(f"TypeScript目标版本建议使用ES2022, 当前为{target}")
        else:
            self.logger.info("✅ TypeScript目标版本: %s", target)

    def validate_eslint_config(self) -> None:
        """验证ESLint配置符合设计文档"""
        self.logger.info("\n🔧 验证ESLint配置...")

        eslint_file = self.project_root / ".eslintrc.cjs"
        if not eslint_file.exists():
            self.errors.append("缺少.eslintrc.cjs配置文件")
            return

        content = eslint_file.read_text(encoding="utf-8")

        # 验证必需的扩展
        required_extends = [
            "@typescript-eslint/recommended",
            "@typescript-eslint/strict",
            "plugin:react-hooks/recommended",
        ]

        for extend in required_extends:
            if extend not in content:
                self.errors.append(f"ESLint配置中缺少扩展: {extend}")
            else:
                self.logger.info("✅ ESLint扩展: %s", extend)

        # 验证严格规则
        strict_rules = [
            "@typescript-eslint/no-explicit-any",
            "@typescript-eslint/explicit-function-return-type",
            "react-hooks/exhaustive-deps",
        ]

        for rule in strict_rules:
            if rule not in content:
                self.errors.append(f"ESLint配置中缺少严格规则: {rule}")
            else:
                self.logger.info("✅ ESLint严格规则: %s", rule)

    def validate_docker_config(self) -> None:
        """验证Docker配置符合设计文档"""
        self.logger.info("\n🐳 验证Docker配置...")

        docker_compose_file = self.project_root / "docker-compose.yml"
        if not docker_compose_file.exists():
            self.errors.append("缺少docker-compose.yml配置文件")
            return

        content = docker_compose_file.read_text(encoding="utf-8")

        # 验证必需的服务
        required_services = [
            "cet4-app",  # FastAPI应用
            "cet4-postgres",  # PostgreSQL数据库
            "cet4-redis",  # Redis缓存
            "cet4-milvus",  # Milvus向量数据库
            "cet4-minio",  # MinIO对象存储
            "cet4-nginx",  # Nginx反向代理
        ]

        for service in required_services:
            if service not in content:
                self.errors.append(f"Docker配置中缺少服务: {service}")
            else:
                self.logger.info("✅ Docker服务: %s", service)

        # 验证端口配置
        required_ports = [
            "8000:8000",  # FastAPI应用
            "3000:3000",  # 前端应用
            "5432:5432",  # PostgreSQL
            "6379:6379",  # Redis
            "19530:19530",  # Milvus
            "9000:9000",  # MinIO
        ]

        for port in required_ports:
            if port not in content:
                self.warnings.append(f"Docker配置中可能缺少端口映射: {port}")
            else:
                self.logger.info("✅ Docker端口: %s", port)

        # 验证网络配置
        if "cet4_learning_network" not in content:
            self.errors.append("Docker配置中缺少独立网络: cet4_learning_network")
        else:
            self.logger.info("✅ Docker独立网络: cet4_learning_network")

    def _validate_python_dependencies(self) -> None:
        """验证Python依赖版本"""
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            return

        content = requirements_file.read_text(encoding="utf-8")

        # 关键依赖版本检查
        key_versions = {
            "fastapi": "0.104",
            "sqlalchemy": "2.0",
            "pydantic": "2.",
            "redis": "5.",
            "pymilvus": "2.3",
        }

        for package, min_version in key_versions.items():
            pattern = rf"{package}==([\d.]+)"
            match = re.search(pattern, content)
            if match:
                version = match.group(1)
                if version.startswith(min_version):
                    self.logger.info("✅ %s版本: %s", package, version)
                else:
                    self.warnings.append(
                        f"{package}版本可能过低: {version} (建议>={min_version})",
                    )
            else:
                self.warnings.append(f"未找到{package}版本信息")

    def _validate_nodejs_dependencies(self) -> None:
        """验证Node.js依赖版本"""
        package_json_file = self.project_root / "package.json"
        if not package_json_file.exists():
            return

        try:
            content = package_json_file.read_text(encoding="utf-8")
            package_data = json.loads(content)
        except json.JSONDecodeError:
            self.errors.append("package.json格式错误")
            return

        dependencies = {
            **package_data.get("dependencies", {}),
            **package_data.get("devDependencies", {}),
        }

        # 关键依赖版本检查
        key_versions = {
            "react": "^18.",
            "typescript": "^5.",
            "@mantine/core": "^7.",
            "vite": "^5.",
            "zustand": "^4.",
        }

        for package, expected_pattern in key_versions.items():
            actual_version = dependencies.get(package)
            if actual_version:
                if actual_version.startswith(expected_pattern):
                    self.logger.info("✅ %s版本: %s", package, actual_version)
                else:
                    msg = f"{package}版本不匹配: {actual_version} " f"(期望{expected_pattern})"
                    self.warnings.append(msg)
            else:
                self.errors.append(f"缺少关键依赖: {package}")

    def validate_dependency_versions(self) -> None:
        """验证依赖版本符合设计文档"""
        self.logger.info("\n📦 验证依赖版本...")

        # 验证Python依赖版本
        self._validate_python_dependencies()

        # 验证Node.js依赖版本
        self._validate_nodejs_dependencies()

    def validate_quality_tools(self) -> None:
        """验证质量工具配置"""
        self.logger.info("\n🛠️ 验证质量工具配置...")

        # 验证package.json中的脚本
        package_json_file = self.project_root / "package.json"
        if not package_json_file.exists():
            return

        try:
            content = package_json_file.read_text(encoding="utf-8")
            package_data = json.loads(content)
        except json.JSONDecodeError:
            return

        scripts = package_data.get("scripts", {})

        # 必需的脚本
        required_scripts = {
            "lint": "ESLint检查",
            "type-check": "TypeScript类型检查",
            "test": "测试脚本",
            "backend:lint": "后端代码检查",
            "quality:check": "质量检查",
        }

        for script, description in required_scripts.items():
            if script in scripts:
                self.logger.info("✅ %s: %s", description, script)
            else:
                self.warnings.append(f"建议添加{description}脚本: {script}")

        self.logger.info("✅ 质量工具配置检查完成")

    def print_results(self) -> None:
        """打印验证结果"""
        separator = "=" * 60
        self.logger.info("\n%s", separator)
        self.logger.info("📊 严格验证结果")
        self.logger.info("%s", separator)

        if self.errors:
            self.logger.info("\n❌ 发现 %d 个错误:", len(self.errors))
            for i, error in enumerate(self.errors, 1):
                self.logger.info("  %d. %s", i, error)

        if self.warnings:
            self.logger.info("\n⚠️ 发现 %d 个警告:", len(self.warnings))
            for i, warning in enumerate(self.warnings, 1):
                self.logger.info("  %d. %s", i, warning)

        if not self.errors and not self.warnings:
            self.logger.info("\n🎉 所有验证通过!")
            self.logger.info("✅ 配置完全符合设计文档v1.0要求")
            self.logger.info("✅ 达到零缺陷交付标准")
        elif not self.errors:
            self.logger.info(
                "\n✅ 核心验证通过, 有 %d 个建议优化项",
                len(self.warnings),
            )
            self.logger.info("✅ 配置基本符合设计文档要求")
        else:
            self.logger.info(
                "\n❌ 验证失败, 需要修复 %d 个错误",
                len(self.errors),
            )
            self.logger.info("❌ 配置不符合零缺陷交付标准")

        self.logger.info("\n📋 验证总结:")
        self.logger.info("  错误: %d", len(self.errors))
        self.logger.info("  警告: %d", len(self.warnings))
        status = "✅ 通过" if len(self.errors) == 0 else "❌ 失败"
        self.logger.info("  状态: %s", status)


def main() -> None:
    """主函数"""
    validator = StrictValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
