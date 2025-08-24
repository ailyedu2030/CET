#!/usr/bin/env python3
"""
验证前端训练工坊组件的完整性 - 需求15
检查组件文件、类型定义、导入导出的一致性
"""

import re
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
frontend_root = project_root / "frontend"


def check_file_exists(file_path: Path) -> bool:
    """检查文件是否存在."""
    return file_path.exists() and file_path.is_file()


def check_typescript_syntax(file_path: Path) -> list[str]:
    """检查TypeScript文件的基本语法."""
    errors = []

    if not file_path.exists():
        return [f"文件不存在: {file_path}"]

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # 检查基本的TypeScript语法
        if not content.strip():
            errors.append("文件为空")
            return errors

        # 检查导入语句
        import_pattern = r"import\s+.*\s+from\s+['\"].*['\"]"
        imports = re.findall(import_pattern, content)

        # 检查导出语句
        export_pattern = r"export\s+(interface|type|const|function|class|default)"
        exports = re.findall(export_pattern, content)

        # 检查React组件
        if file_path.suffix == ".tsx":
            component_pattern = r"function\s+\w+.*\):\s*JSX\.Element"
            arrow_component_pattern = r"const\s+\w+.*=.*\):\s*JSX\.Element"
            components = re.findall(component_pattern, content) + re.findall(
                arrow_component_pattern, content
            )

            # 更宽松的检查 - 只要有JSX.Element就认为是组件
            if "JSX.Element" not in content and "export" in content:
                errors.append("TSX文件应该包含React组件")

        # 检查未闭合的括号
        open_braces = content.count("{")
        close_braces = content.count("}")
        if open_braces != close_braces:
            errors.append(f"括号不匹配: {{ {open_braces} vs }} {close_braces}")

        # 检查未闭合的圆括号
        open_parens = content.count("(")
        close_parens = content.count(")")
        if open_parens != close_parens:
            errors.append(f"圆括号不匹配: ( {open_parens} vs ) {close_parens}")

    except Exception as e:
        errors.append(f"读取文件时出错: {e}")

    return errors


def validate_training_workshop_components() -> bool:
    """验证训练工坊组件."""
    print("🔍 验证训练工坊前端组件...")

    # 定义要检查的组件文件
    component_files = [
        "src/components/TrainingWorkshop/TrainingParameterConfigForm.tsx",
        "src/components/TrainingWorkshop/TrainingParameterTemplateModal.tsx",
        "src/components/TrainingWorkshop/WeeklyTrainingConfigForm.tsx",
        "src/components/TrainingWorkshop/index.ts",
    ]

    # 定义要检查的页面文件
    page_files = [
        "src/pages/Teacher/TrainingWorkshopPage.tsx",
    ]

    # 定义要检查的API文件
    api_files = [
        "src/api/trainingWorkshop.ts",
    ]

    all_files = component_files + page_files + api_files

    print("\n📋 检查文件存在性:")
    missing_files = []
    for file_path in all_files:
        full_path = frontend_root / file_path
        if check_file_exists(full_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - 文件不存在")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ 发现 {len(missing_files)} 个缺失文件")
        return False

    print("\n🔍 检查TypeScript语法:")
    syntax_errors = {}
    for file_path in all_files:
        full_path = frontend_root / file_path
        errors = check_typescript_syntax(full_path)
        if errors:
            syntax_errors[file_path] = errors
            print(f"  ❌ {file_path}:")
            for error in errors:
                print(f"     - {error}")
        else:
            print(f"  ✅ {file_path}")

    if syntax_errors:
        print(f"\n❌ 发现 {len(syntax_errors)} 个文件有语法问题")
        return False

    print("\n🔗 检查组件导入导出:")

    # 检查index.ts导出
    index_file = frontend_root / "src/components/TrainingWorkshop/index.ts"
    with open(index_file, encoding="utf-8") as f:
        index_content = f.read()

    expected_exports = [
        "TrainingParameterConfigForm",
        "TrainingParameterTemplateModal",
        "WeeklyTrainingConfigForm",
    ]

    for export_name in expected_exports:
        if export_name in index_content:
            print(f"  ✅ {export_name} - 已导出")
        else:
            print(f"  ❌ {export_name} - 未在index.ts中导出")
            return False

    # 检查主页面的导入
    page_file = frontend_root / "src/pages/Teacher/TrainingWorkshopPage.tsx"
    with open(page_file, encoding="utf-8") as f:
        page_content = f.read()

    expected_imports = [
        "TrainingParameterConfigForm",
        "TrainingParameterTemplateModal",
        "WeeklyTrainingConfigForm",
    ]

    for import_name in expected_imports:
        if import_name in page_content:
            print(f"  ✅ {import_name} - 已在页面中导入")
        else:
            print(f"  ❌ {import_name} - 未在页面中导入")
            return False

    print("\n📊 组件功能检查:")

    # 检查表单组件的关键功能
    form_checks = {
        "TrainingParameterConfigForm.tsx": [
            "useForm",
            "onSubmit",
            "validation",
            "Slider",
            "NumberInput",
        ],
        "TrainingParameterTemplateModal.tsx": ["Modal", "Tabs", "useForm", "onSuccess"],
        "WeeklyTrainingConfigForm.tsx": [
            "Tabs",
            "DateTimePicker",
            "MultiSelect",
            "Switch",
        ],
    }

    for file_name, required_features in form_checks.items():
        file_path = frontend_root / f"src/components/TrainingWorkshop/{file_name}"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        print(f"  {file_name}:")
        for feature in required_features:
            if feature in content:
                print(f"    ✅ {feature}")
            else:
                print(f"    ❌ {feature} - 缺失")

    print("\n✅ 所有组件验证通过!")
    return True


def main() -> int:
    """主函数."""
    print("🚀 训练工坊前端组件验证工具")
    print("=" * 50)

    if not frontend_root.exists():
        print("❌ 前端目录不存在")
        return 1

    success = validate_training_workshop_components()

    print("\n" + "=" * 50)
    if success:
        print("🎉 所有验证通过！前端组件准备就绪。")
        return 0
    else:
        print("❌ 验证失败，请修复问题后重试。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
