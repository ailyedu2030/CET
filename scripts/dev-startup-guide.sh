#!/bin/bash

# 英语四级学习系统 - 开发启动指南
# 基于Cursor Specs智能查询系统的完整开发流程

set -e

echo "🚀 英语四级学习系统 - 开发启动指南"
echo "=================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 已安装${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 未安装${NC}"
        return 1
    fi
}

# 第一步：环境检查
echo -e "\n${BLUE}📋 第一步：检查开发环境${NC}"
echo "----------------------------------------"

# 检查必需工具
MISSING_TOOLS=()

if ! check_command "python3"; then
    MISSING_TOOLS+=("python3")
fi

if ! check_command "node"; then
    MISSING_TOOLS+=("node")
fi

if ! check_command "npm"; then
    MISSING_TOOLS+=("npm")
fi

if ! check_command "docker"; then
    MISSING_TOOLS+=("docker")
fi

if ! check_command "docker-compose"; then
    MISSING_TOOLS+=("docker-compose")
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo -e "${GREEN}✅ Python版本符合要求: $PYTHON_VERSION (需要 ≥3.11)${NC}"
else
    echo -e "${RED}❌ Python版本不符合要求: $PYTHON_VERSION (需要 ≥3.11)${NC}"
    MISSING_TOOLS+=("python3.11+")
fi

# 检查Node版本
NODE_VERSION=$(node --version 2>&1 | sed 's/v//')
NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)

if [ "$NODE_MAJOR" -ge 18 ]; then
    echo -e "${GREEN}✅ Node.js版本符合要求: v$NODE_VERSION (需要 ≥18)${NC}"
else
    echo -e "${RED}❌ Node.js版本不符合要求: v$NODE_VERSION (需要 ≥18)${NC}"
    MISSING_TOOLS+=("node18+")
fi

# 如果有缺失工具，提供安装指导
if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo -e "\n${RED}⚠️  发现缺失的工具，请先安装：${NC}"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo -e "${YELLOW}   - $tool${NC}"
    done
    echo -e "\n${BLUE}💡 安装建议：${NC}"
    echo "   macOS: brew install python@3.11 node docker docker-compose"
    echo "   Ubuntu: apt-get install python3.11 nodejs npm docker.io docker-compose"
    echo ""
    echo -e "${YELLOW}请安装缺失工具后重新运行此脚本${NC}"
    exit 1
fi

# 第二步：项目依赖检查
echo -e "\n${BLUE}📦 第二步：检查项目依赖${NC}"
echo "----------------------------------------"

# 检查Python依赖
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✅ requirements.txt 存在${NC}"
    echo "   主要依赖预览："
    head -5 requirements.txt | sed 's/^/   /'
else
    echo -e "${RED}❌ requirements.txt 不存在${NC}"
fi

# 检查前端依赖
if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}✅ frontend/package.json 存在${NC}"
    echo "   React版本: $(grep '"react"' frontend/package.json | cut -d'"' -f4)"
else
    echo -e "${RED}❌ frontend/package.json 不存在${NC}"
fi

# 检查Docker配置
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✅ docker-compose.yml 存在${NC}"
    echo "   服务数量: $(grep -c 'image:\|build:' docker-compose.yml)"
else
    echo -e "${RED}❌ docker-compose.yml 不存在${NC}"
fi

# 第三步：Cursor Specs系统验证
echo -e "\n${BLUE}🎯 第三步：验证Cursor Specs系统${NC}"
echo "----------------------------------------"

if [ -f ".cursor/specs-core-navigator.md" ]; then
    echo -e "${GREEN}✅ Cursor Specs导航系统已配置${NC}"

    # 运行验证脚本
    if npm run cursor:verify-specs > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Specs系统验证通过${NC}"
    else
        echo -e "${YELLOW}⚠️  Specs系统验证有警告，但可以继续开发${NC}"
    fi
else
    echo -e "${RED}❌ Cursor Specs系统未配置${NC}"
fi

# 第四步：开发流程指导
echo -e "\n${BLUE}🚀 第四步：开发流程指导${NC}"
echo "----------------------------------------"

echo -e "${GREEN}恭喜！您的开发环境已就绪！${NC}"
echo ""
echo -e "${BLUE}📋 推荐的开发流程：${NC}"
echo ""
echo "1️⃣  在Cursor Chat中查询第一阶段任务："
echo -e "${YELLOW}   \"从tasks.md第44-223行查看第一阶段基础架构任务\"${NC}"
echo ""
echo "2️⃣  获取具体需求规范："
echo -e "${YELLOW}   \"从requirements.md第169-343行提取管理员端需求1-9\"${NC}"
echo ""
echo "3️⃣  查看技术设计方案："
echo -e "${YELLOW}   \"从design.md第15-88行提取系统架构概览\"${NC}"
echo ""
echo "4️⃣  开始编码实现："
echo "   - 使用Cursor AI进行智能编码"
echo "   - 遵循零缺陷开发标准"
echo "   - 实时验证代码质量"
echo ""

# 第五步：快速启动选项
echo -e "${BLUE}⚡ 第五步：快速启动选项${NC}"
echo "----------------------------------------"

echo "选择您的开发方式："
echo ""
echo "A) 🏗️  从基础架构开始 (推荐新手)"
echo "   npm run dev:setup-basic"
echo ""
echo "B) 🎯 直接开发核心功能 (有经验开发者)"
echo "   npm run dev:setup-core"
echo ""
echo "C) 🐳 使用Docker环境 (完整环境)"
echo "   npm run dev:setup-docker"
echo ""
echo "D) 📚 查看完整开发指南"
echo "   cat .cursor/cursor-specs-usage-guide.md"
echo ""

# 第六步：实用命令
echo -e "${BLUE}🔧 第六步：实用开发命令${NC}"
echo "----------------------------------------"

echo "验证和测试："
echo "  npm run cursor:verify-specs    # 验证Specs系统"
echo "  npm run cursor:test            # 测试Cursor规则"
echo "  npm run quality:check          # 代码质量检查"
echo ""
echo "开发服务："
echo "  npm run dev:backend            # 启动后端服务"
echo "  npm run dev:frontend           # 启动前端服务"
echo "  npm run dev:full               # 同时启动前后端"
echo ""
echo "Docker操作："
echo "  docker-compose up -d           # 启动所有服务"
echo "  docker-compose logs -f         # 查看日志"
echo "  docker-compose down            # 停止服务"
echo ""

# 第七步：Cursor使用技巧
echo -e "${BLUE}💡 第七步：Cursor开发技巧${NC}"
echo "----------------------------------------"

echo "在Cursor Chat中的高效查询："
echo ""
echo "🎯 需求查询："
echo -e "${YELLOW}   \"基于需求21实现学生综合训练中心\"${NC}"
echo ""
echo "🏗️ 设计查询："
echo -e "${YELLOW}   \"根据design.md第189-370行实现核心模块\"${NC}"
echo ""
echo "📋 任务查询："
echo -e "${YELLOW}   \"按照tasks.md第44-223行搭建基础架构\"${NC}"
echo ""
echo "✅ 验证查询："
echo -e "${YELLOW}   \"验证我的实现是否符合需求规范\"${NC}"
echo ""

echo -e "${GREEN}🎉 开发启动指南完成！祝您开发顺利！${NC}"
echo ""
echo -e "${BLUE}💬 如需帮助，请在Cursor Chat中询问具体问题${NC}"

