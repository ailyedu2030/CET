#!/bin/bash

# 前端代码质量检查脚本

echo "🔍 开始前端代码质量检查..."

# 1. ESLint检查
echo "📋 运行ESLint检查..."
npm run lint
if [ $? -ne 0 ]; then
    echo "❌ ESLint检查失败"
    exit 1
fi

# 2. TypeScript类型检查
echo "🔧 运行TypeScript类型检查..."
npm run type-check
if [ $? -ne 0 ]; then
    echo "❌ TypeScript类型检查失败"
    exit 1
fi

# 3. Prettier格式检查
echo "💅 运行Prettier格式检查..."
npm run format:check
if [ $? -ne 0 ]; then
    echo "❌ Prettier格式检查失败"
    exit 1
fi

# 4. 循环依赖检查
echo "🔄 检查循环依赖..."
npx madge --circular src/
if [ $? -ne 0 ]; then
    echo "❌ 发现循环依赖"
    exit 1
fi

# 5. 构建测试
echo "🏗️ 测试构建..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ 构建失败"
    exit 1
fi

echo "✅ 所有前端代码质量检查通过！"