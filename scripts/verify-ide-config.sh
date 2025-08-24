#!/bin/bash
set -e

echo "🔍 验证IDE和mypy配置状态"
echo "============================="

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境未找到"
    exit 1
fi

echo ""
echo "1. 检查mypy配置文件..."
if grep -q "disable_error_code.*misc" pyproject.toml; then
    echo "✅ pyproject.toml中已禁用misc错误"
else
    echo "❌ pyproject.toml中misc错误配置缺失"
fi

echo ""
echo "2. 检查VS Code配置..."
if [ -f ".vscode/settings.json" ]; then
    if grep -q "mypyArgs" .vscode/settings.json; then
        echo "✅ VS Code mypy参数配置正确"
    else
        echo "❌ VS Code mypy参数配置缺失"
    fi
else
    echo "❌ VS Code配置文件不存在"
fi

echo ""
echo "3. 检查工作区配置..."
if [ -f "CET.code-workspace" ]; then
    echo "✅ 工作区配置文件存在"
else
    echo "❌ 工作区配置文件缺失"
fi

echo ""
echo "4. 运行mypy检查..."
echo "   命令行mypy结果："
if mypy . --config-file=pyproject.toml --show-error-codes; then
    echo "✅ 命令行mypy检查通过"
else
    echo "❌ 命令行mypy检查失败"
fi

echo ""
echo "5. 检查常见框架的类型问题..."
echo "   测试Celery装饰器类型检查..."
python3 -c "
try:
    import mypy.api
    result = mypy.api.run(['app/shared/tasks/email_tasks.py', '--config-file=pyproject.toml', '--show-error-codes'])
    if 'error:' in result[0]:
        print('❌ Celery任务文件仍有类型错误')
        print(result[0])
    else:
        print('✅ Celery任务文件类型检查通过')
except Exception as e:
    print(f'⚠️  无法运行mypy API: {e}')
"

echo ""
echo "6. 检查SQLAlchemy模型类型问题..."
python3 -c "
try:
    import mypy.api
    result = mypy.api.run(['app/shared/models/base_model.py', '--config-file=pyproject.toml', '--show-error-codes'])
    if 'error:' in result[0]:
        print('❌ SQLAlchemy模型文件仍有类型错误')
        print(result[0])
    else:
        print('✅ SQLAlchemy模型文件类型检查通过')
except Exception as e:
    print(f'⚠️  无法运行mypy API: {e}')
"

echo ""
echo "📋 IDE优化建议："
echo "================================"
echo ""
echo "🎯 如果IDE仍显示misc错误，请执行以下操作："
echo ""
echo "A. 重新加载VS Code："
echo "   1. 按 Cmd+Shift+P (macOS) 或 Ctrl+Shift+P (Windows/Linux)"
echo "   2. 输入并选择: Developer: Reload Window"
echo ""
echo "B. 使用工作区文件："
echo "   1. 关闭当前文件夹"
echo "   2. 使用 File -> Open Workspace 打开 CET.code-workspace"
echo ""
echo "C. 检查Python解释器："
echo "   1. 按 Cmd+Shift+P"
echo "   2. 输入: Python: Select Interpreter"
echo "   3. 选择: ./.venv/bin/python"
echo ""
echo "D. 重新安装mypy扩展："
echo "   1. 在Extensions面板卸载 mypy-type-checker"
echo "   2. 重新安装并重启VS Code"
echo ""
echo "E. 手动清理并重启："
echo "   bash scripts/clean-ide-cache.sh"
echo "   然后完全重启VS Code (不是重新加载)"
echo ""
echo "🔍 如果问题持续存在，请检查："
echo "   - IDE是否使用了全局mypy配置而非项目配置"
echo "   - 是否有其他Python linter与mypy冲突"
echo "   - VS Code的Python扩展是否为最新版本"
echo ""

