#!/bin/bash
set -e

echo "🧹 清理IDE和mypy缓存以解决类型检查问题"
echo "========================================"

# 1. 清理Python缓存
echo "1. 清理Python缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# 2. 清理mypy缓存
echo "2. 清理mypy缓存..."
rm -rf .mypy_cache 2>/dev/null || true

# 3. 清理ruff缓存
echo "3. 清理ruff缓存..."
rm -rf .ruff_cache 2>/dev/null || true

# 4. 清理VS Code缓存
echo "4. 清理VS Code缓存..."
if [ -d ".vscode" ]; then
    rm -rf .vscode/.ropeproject 2>/dev/null || true
    # 不删除settings.json，只清理临时文件
fi

# 5. 重新生成mypy缓存
echo "5. 重新初始化mypy缓存..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "   - 运行mypy预检查..."
    mypy . --config-file=pyproject.toml --show-error-codes > /dev/null 2>&1 || true
    echo "   ✅ mypy缓存已重新生成"
else
    echo "   ⚠️  虚拟环境未找到，跳过mypy缓存初始化"
fi

echo ""
echo "✅ 缓存清理完成！"
echo ""
echo "📋 接下来的操作步骤："
echo "   1. 重启VS Code或重新加载窗口 (Cmd+Shift+P -> Developer: Reload Window)"
echo "   2. 打开 CET.code-workspace 工作区文件而不是文件夹"
echo "   3. 确认Python解释器指向 ./.venv/bin/python"
echo "   4. 等待几分钟让扩展重新初始化"
echo ""
echo "🔧 验证IDE配置："
echo "   运行: bash scripts/verify-ide-config.sh"
echo ""

