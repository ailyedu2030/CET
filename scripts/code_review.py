#!/usr/bin/env python3
"""
全面代码审查工具 - 零缺陷标准
检查所有配置文件、代码文件的语法、格式和质量问题
"""

import json
import os
import subprocess
import sys
from pathlib import Path


class CodeReviewer:
    """代码审查器 - 零缺陷标准"""

    def __init__(self) -> None:
        self.project_root = Path.cwd()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.fixed_issues: list[str] = []

    def review_all(self) -> bool:
        """执行全面代码审查"""
        print("🔍 全面代码审查 - 零缺陷标准")
        print("=" * 70)

        # 1. JSON文件语法检查
        self.check_json_syntax()

        # 2. Python文件语法检查
        self.check_python_syntax()

        # 3. TypeScript配置检查
        self.check_typescript_config()

        # 4. Docker配置检查
        self.check_docker_config()

        # 5. 脚本文件权限检查
        self.check_script_permissions()

        # 6. 文件编码检查
        self.check_file_encoding()

        # 7. 行尾符检查
        self.check_line_endings()

        # 8. 配置一致性检查
        self.check_config_consistency()

        # 打印结果
        self.print_review_results()

        return len(self.errors) == 0

    def check_json_syntax(self) -> None:
        """检查JSON文件语法"""
        print("\n📄 检查JSON文件语法...")

        json_files = [
            "package.json",
            ".vscode/settings.json",
            ".vscode/extensions.json",
            "frontend/tsconfig.json",
            "frontend/tsconfig.node.json",
        ]

        for json_file in json_files:
            file_path = self.project_root / json_file
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        json.load(f)
                    print(f"✅ {json_file}: 语法正确")
                except json.JSONDecodeError as e:
                    self.errors.append(f"{json_file}: JSON语法错误 - {e}")
                except Exception as e:
                    self.errors.append(f"{json_file}: 读取错误 - {e}")
            else:
                self.warnings.append(f"{json_file}: 文件不存在")

    def check_python_syntax(self) -> None:
        """检查Python文件语法"""
        print("\n🐍 检查Python文件语法...")

        python_files: list[Path] = []
        for pattern in ["**/*.py"]:
            python_files.extend(self.project_root.glob(pattern))

        for py_file in python_files:
            if "/.venv/" in str(py_file) or "/venv/" in str(py_file):
                continue

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    print(f"✅ {py_file.relative_to(self.project_root)}: 语法正确")
                else:
                    self.errors.append(
                        f"{py_file.relative_to(self.project_root)}: 语法错误 - {result.stderr}",
                    )
            except Exception as e:
                self.errors.append(
                    f"{py_file.relative_to(self.project_root)}: 检查失败 - {e}",
                )

    def check_typescript_config(self) -> None:
        """检查TypeScript配置"""
        print("\n📘 检查TypeScript配置...")

        tsconfig_files = [
            "frontend/tsconfig.json",
            "frontend/tsconfig.node.json",
        ]

        for tsconfig in tsconfig_files:
            file_path = self.project_root / tsconfig
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        config = json.load(f)

                    # 检查必需的编译选项
                    compiler_options = config.get("compilerOptions", {})

                    if tsconfig == "frontend/tsconfig.json":
                        # 主配置文件的严格检查
                        required_options = {
                            "strict": True,
                            "noImplicitAny": True,
                            "noUnusedLocals": True,
                            "noUnusedParameters": True,
                        }

                        for option, expected in required_options.items():
                            actual = compiler_options.get(option)
                            if actual != expected:
                                self.warnings.append(
                                    f"{tsconfig}: {option}应为{expected}，实际为{actual}",
                                )

                    print(f"✅ {tsconfig}: 配置正确")

                except json.JSONDecodeError as e:
                    self.errors.append(f"{tsconfig}: JSON语法错误 - {e}")
                except Exception as e:
                    self.errors.append(f"{tsconfig}: 检查失败 - {e}")

    def check_docker_config(self) -> None:
        """检查Docker配置"""
        print("\n🐳 检查Docker配置...")

        # 检查docker-compose.yml语法
        try:
            result = subprocess.run(
                ["docker-compose", "config"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                print("✅ docker-compose.yml: 语法正确")
                if result.stderr:
                    # 检查是否有警告
                    if "WARN" in result.stderr:
                        self.warnings.append(
                            f"Docker Compose警告: {result.stderr.strip()}",
                        )
            else:
                self.errors.append(f"docker-compose.yml: 语法错误 - {result.stderr}")
        except FileNotFoundError:
            self.warnings.append("docker-compose命令未找到，跳过Docker配置检查")
        except Exception as e:
            self.errors.append(f"Docker配置检查失败: {e}")

    def check_script_permissions(self) -> None:
        """检查脚本文件权限"""
        print("\n🔧 检查脚本文件权限...")

        script_files = [
            "scripts/install_dependencies.sh",
            "scripts/check_dependencies.py",
            "scripts/strict_validate.py",
        ]

        for script in script_files:
            file_path = self.project_root / script
            if file_path.exists():
                # 检查是否有执行权限
                if os.access(file_path, os.X_OK):
                    print(f"✅ {script}: 权限正确")
                else:
                    # 自动修复权限
                    try:
                        os.chmod(file_path, 0o755)
                        self.fixed_issues.append(f"{script}: 已修复执行权限")
                        print(f"🔧 {script}: 已修复执行权限")
                    except Exception as e:
                        self.errors.append(f"{script}: 权限修复失败 - {e}")
            else:
                self.warnings.append(f"{script}: 文件不存在")

    def check_file_encoding(self) -> None:
        """检查文件编码"""
        print("\n📝 检查文件编码...")

        text_files: list[Path] = []
        for pattern in [
            "**/*.py",
            "**/*.ts",
            "**/*.tsx",
            "**/*.json",
            "**/*.md",
            "**/*.yml",
            "**/*.yaml",
        ]:
            text_files.extend(self.project_root.glob(pattern))

        encoding_issues = 0
        for file_path in text_files:
            if "/.venv/" in str(file_path) or "/node_modules/" in str(file_path):
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    f.read()
            except UnicodeDecodeError:
                self.errors.append(
                    f"{file_path.relative_to(self.project_root)}: 编码不是UTF-8",
                )
                encoding_issues += 1
            except Exception:
                continue

        if encoding_issues == 0:
            print("✅ 所有文件编码正确 (UTF-8)")
        else:
            print(f"❌ 发现 {encoding_issues} 个编码问题")

    def check_line_endings(self) -> None:
        """检查行尾符一致性"""
        print("\n📏 检查行尾符一致性...")

        # 检查关键配置文件的行尾符
        key_files = [
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            ".eslintrc.cjs",
            ".prettierrc",
        ]

        line_ending_issues = 0
        for file_name in key_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()

                    # 检查是否有Windows行尾符 (\r\n)
                    if b"\r\n" in content:
                        self.warnings.append(
                            f"{file_name}: 包含Windows行尾符，建议使用LF",
                        )
                        line_ending_issues += 1
                    else:
                        print(f"✅ {file_name}: 行尾符正确 (LF)")
                except Exception:
                    continue

        if line_ending_issues == 0:
            print("✅ 所有文件行尾符一致")

    def check_config_consistency(self) -> None:
        """检查配置一致性"""
        print("\n🔄 检查配置一致性...")

        # 检查Python版本一致性
        try:
            # 检查pyproject.toml中的Python版本
            with open(self.project_root / "pyproject.toml", encoding="utf-8") as f:
                pyproject_content = f.read()

            if 'target-version = "py311"' in pyproject_content:
                print("✅ pyproject.toml: Python版本配置一致")
            else:
                self.warnings.append("pyproject.toml: Python版本配置可能不一致")

        except Exception as e:
            self.warnings.append(f"无法检查pyproject.toml: {e}")

        # 检查Node.js版本一致性
        try:
            with open(self.project_root / "package.json", encoding="utf-8") as f:
                package_data = json.load(f)

            engines = package_data.get("engines", {})
            node_version = engines.get("node")
            npm_version = engines.get("npm")

            if node_version and node_version.startswith(">=18"):
                print("✅ package.json: Node.js版本配置一致")
            else:
                self.warnings.append("package.json: Node.js版本配置可能不一致")

            if npm_version and npm_version.startswith(">=9"):
                print("✅ package.json: npm版本配置一致")
            else:
                self.warnings.append("package.json: npm版本配置可能不一致")

        except Exception as e:
            self.warnings.append(f"无法检查package.json: {e}")

    def print_review_results(self) -> None:
        """打印审查结果"""
        print("\n" + "=" * 70)
        print("📊 代码审查结果")
        print("=" * 70)

        if self.fixed_issues:
            print(f"\n🔧 自动修复 {len(self.fixed_issues)} 个问题:")
            for i, fix in enumerate(self.fixed_issues, 1):
                print(f"  {i}. {fix}")

        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️ 发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            print("\n🎉 代码审查完全通过！")
            print("✅ 所有文件语法正确")
            print("✅ 所有配置格式正确")
            print("✅ 达到零缺陷标准")
        elif not self.errors:
            print(f"\n✅ 核心审查通过，有 {len(self.warnings)} 个优化建议")
            print("✅ 代码质量达标")
        else:
            print(f"\n❌ 审查失败，需要修复 {len(self.errors)} 个错误")
            print("❌ 代码质量不达标")

        # 提供修复建议
        if self.errors or self.warnings:
            print("\n🛠️ 修复建议:")
            print("-" * 50)

            if self.errors:
                print("1. 修复所有错误后重新运行审查")
                print("2. 检查文件语法和格式")
                print("3. 验证配置文件完整性")

            if self.warnings:
                print("4. 考虑优化警告项以提高代码质量")
                print("5. 统一文件格式和编码")

        print("\n📋 审查总结:")
        print(f"  自动修复: {len(self.fixed_issues)}")
        print(f"  错误: {len(self.errors)}")
        print(f"  警告: {len(self.warnings)}")
        print(f"  状态: {'✅ 通过' if len(self.errors) == 0 else '❌ 失败'}")


def main() -> None:
    """主函数"""
    reviewer = CodeReviewer()
    success = reviewer.review_all()

    if success:
        print("\n🚀 代码审查通过，可以继续开发！")
    else:
        print("\n⚠️ 请修复发现的问题后重新运行审查")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
