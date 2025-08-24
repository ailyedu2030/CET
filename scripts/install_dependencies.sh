#!/bin/bash
# 英语四级学习系统依赖安装脚本
# 基于设计文档v1.0，零缺陷交付标准

set -e  # 任何命令失败都退出

echo "🚀 英语四级学习系统依赖安装"
echo "=================================="
echo "设计文档版本: v1.0"
echo "安装标准: 零缺陷交付"
echo ""

# 检查系统要求
echo "🔧 检查系统要求..."
echo "----------------------------------"

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 11 ]); then
    echo "❌ Python版本过低: $python_version (需要 >=3.11)"
    echo "请升级Python版本后重试"
    exit 1
else
    echo "✅ Python版本: $python_version (符合要求)"
fi

# 检查Node.js版本
if command -v node >/dev/null 2>&1; then
    node_version=$(node --version | grep -oE '[0-9]+' | head -1)
    if [ "$node_version" -lt 18 ]; then
        echo "❌ Node.js版本过低: v$node_version (需要 >=18)"
        echo "请升级Node.js版本后重试"
        exit 1
    else
        echo "✅ Node.js版本: v$node_version (符合要求)"
    fi
else
    echo "❌ 未找到Node.js，请先安装Node.js >=18"
    exit 1
fi

# 检查npm版本
if command -v npm >/dev/null 2>&1; then
    npm_version=$(npm --version | grep -oE '[0-9]+' | head -1)
    if [ "$npm_version" -lt 9 ]; then
        echo "⚠️ npm版本较低: v$npm_version (推荐 >=9)"
        echo "建议升级: npm install -g npm@latest"
    else
        echo "✅ npm版本: v$npm_version (符合要求)"
    fi
else
    echo "❌ 未找到npm"
    exit 1
fi

echo ""

# 选择安装方式
echo "📦 选择安装方式:"
echo "----------------------------------"
echo "1. Docker一键部署 (推荐)"
echo "2. 本地开发环境安装"
echo "3. 仅安装Python依赖"
echo "4. 仅安装Node.js依赖"
echo ""

read -p "请选择安装方式 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🐳 Docker一键部署..."
        echo "----------------------------------"
        
        # 检查Docker
        if ! command -v docker >/dev/null 2>&1; then
            echo "❌ 未找到Docker，请先安装Docker"
            exit 1
        fi
        
        if ! command -v docker-compose >/dev/null 2>&1; then
            echo "❌ 未找到docker-compose，请先安装docker-compose"
            exit 1
        fi
        
        echo "✅ Docker环境检查通过"
        echo ""
        echo "🚀 启动Docker服务..."
        
        # 构建并启动服务
        docker-compose down 2>/dev/null || true
        docker-compose build
        docker-compose up -d
        
        echo ""
        echo "✅ Docker部署完成！"
        echo ""
        echo "📋 服务访问地址:"
        echo "  前端应用: http://localhost:3000"
        echo "  后端API: http://localhost:8000"
        echo "  API文档: http://localhost:8000/docs"
        echo "  MinIO控制台: http://localhost:9001"
        echo "  Grafana监控: http://localhost:3001"
        echo ""
        echo "🔍 检查服务状态:"
        echo "  docker-compose ps"
        echo "  docker-compose logs -f"
        ;;
        
    2)
        echo ""
        echo "💻 本地开发环境安装..."
        echo "----------------------------------"
        
        # 创建Python虚拟环境
        echo "🐍 设置Python虚拟环境..."
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
            echo "✅ 虚拟环境创建成功"
        else
            echo "✅ 虚拟环境已存在"
        fi
        
        # 激活虚拟环境
        source .venv/bin/activate
        echo "✅ 虚拟环境已激活"
        
        # 升级pip
        echo ""
        echo "📦 升级pip..."
        pip install --upgrade pip
        
        # 安装Python依赖
        echo ""
        echo "🐍 安装Python依赖 (62个包)..."
        pip install -r requirements.txt
        echo "✅ Python依赖安装完成"
        
        # 安装Node.js依赖
        echo ""
        echo "📦 安装Node.js依赖 (59个包)..."
        npm install
        echo "✅ Node.js依赖安装完成"
        
        echo ""
        echo "✅ 本地开发环境安装完成！"
        echo ""
        echo "🚀 启动开发服务:"
        echo "  # 激活虚拟环境"
        echo "  source .venv/bin/activate"
        echo ""
        echo "  # 启动后端 (终端1)"
        echo "  npm run backend:dev"
        echo ""
        echo "  # 启动前端 (终端2)"
        echo "  npm run dev"
        echo ""
        echo "📋 开发服务地址:"
        echo "  前端: http://localhost:3000"
        echo "  后端: http://localhost:8000"
        echo "  API文档: http://localhost:8000/docs"
        ;;
        
    3)
        echo ""
        echo "🐍 安装Python依赖..."
        echo "----------------------------------"
        
        # 创建虚拟环境
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
            echo "✅ 虚拟环境创建成功"
        fi
        
        # 激活虚拟环境
        source .venv/bin/activate
        echo "✅ 虚拟环境已激活"
        
        # 升级pip
        pip install --upgrade pip
        
        # 安装依赖
        echo "📦 安装Python依赖 (62个包)..."
        pip install -r requirements.txt
        
        echo ""
        echo "✅ Python依赖安装完成！"
        echo ""
        echo "🚀 启动后端服务:"
        echo "  source .venv/bin/activate"
        echo "  npm run backend:dev"
        ;;
        
    4)
        echo ""
        echo "📦 安装Node.js依赖..."
        echo "----------------------------------"
        
        npm install
        
        echo ""
        echo "✅ Node.js依赖安装完成！"
        echo ""
        echo "🚀 启动前端服务:"
        echo "  npm run dev"
        ;;
        
    *)
        echo "❌ 无效选择，退出安装"
        exit 1
        ;;
esac

echo ""
echo "🔍 验证安装..."
echo "----------------------------------"

# 运行依赖检查
if [ -f "scripts/check_dependencies.py" ]; then
    echo "运行依赖检查脚本..."
    python3 scripts/check_dependencies.py
else
    echo "⚠️ 依赖检查脚本不存在，跳过验证"
fi

echo ""
echo "🎉 安装完成！"
echo "=================================="
echo ""
echo "📚 下一步操作:"
echo "1. 查看项目文档: README.md"
echo "2. 运行质量检查: npm run quality:check"
echo "3. 运行测试: npm run test"
echo "4. 开始开发: 参考上述启动命令"
echo ""
echo "🆘 如遇问题:"
echo "1. 查看依赖审计报告: DEPENDENCIES_AUDIT.md"
echo "2. 重新运行检查: python3 scripts/check_dependencies.py"
echo "3. 查看Docker日志: docker-compose logs -f"
echo ""
echo "✨ 祝开发顺利！"