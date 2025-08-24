#!/bin/bash
# 质量检查脚本 - 零容忍标准

set -e  # 任何命令失败都退出

echo "🚀 开始零容忍质量检查..."

# 1. Python代码质量检查 (零容忍)
echo "📋 Python代码质量检查 (Ruff + mypy)..."
echo "  - 运行 Ruff 检查..."
ruff check . --output-format=github || {
    echo "❌ Ruff 检查失败 - 必须修复所有问题"
    exit 1
}

echo "  - 运行 mypy 类型检查..."
mypy . --strict || {
    echo "❌ mypy 类型检查失败 - 必须修复所有类型问题"
    exit 1
}

# 2. TypeScript代码质量检查 (零容忍)
echo "📋 TypeScript代码质量检查 (tsc + ESLint)..."

echo "  - 运行 TypeScript 编译检查..."
npm run type-check || {
    echo "❌ TypeScript 编译失败 - 必须修复所有类型错误"
    exit 1
}

echo "  - 运行 ESLint 检查..."
npm run lint || {
    echo "❌ ESLint 检查失败 - 必须修复所有代码规范问题"
    exit 1
}

# 3. 测试覆盖率检查
echo "🧪 测试覆盖率检查..."
echo "  - 运行单元测试..."
pytest tests/unit/ --cov=app --cov-report=term-missing --cov-fail-under=80 || {
    echo "❌ 单元测试覆盖率不足80% - 必须增加测试"
    exit 1
}

echo "  - 运行集成测试..."
pytest tests/integration/ --cov=app --cov-append --cov-report=term-missing --cov-fail-under=70 || {
    echo "❌ 集成测试覆盖率不足70% - 必须增加集成测试"
    exit 1
}

# 4. 前端测试
echo "🧪 前端测试..."
npm run test || {
    echo "❌ 前端测试失败"
    exit 1
}

echo "✅ 所有质量检查通过！代码达到零缺陷标准！"
echo "📊 质量报告："
echo "  - Python代码: ✅ Ruff + mypy 零错误"
echo "  - TypeScript代码: ✅ tsc + ESLint 零错误"
echo "  - 测试覆盖率: ✅ 单元测试>80%, 集成测试>70%"
echo "  - 前端测试: ✅ 通过"