#!/bin/bash

# 英语四级学习系统 - Cursor 规则自动化设置脚本
# 用于快速配置 Cursor IDE 的开发环境和规则文件

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="英语四级学习系统"
VERSION="1.0.0"

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo
    print_message $CYAN "=================================="
    print_message $CYAN "$1"
    print_message $CYAN "=================================="
    echo
}

print_step() {
    print_message $BLUE "🔧 $1"
}

print_success() {
    print_message $GREEN "✅ $1"
}

print_warning() {
    print_message $YELLOW "⚠️  $1"
}

print_error() {
    print_message $RED "❌ $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "命令 '$1' 未找到，请先安装"
        return 1
    fi
    return 0
}

# 检查文件是否存在
check_file() {
    if [ ! -f "$1" ]; then
        print_error "文件 '$1' 不存在"
        return 1
    fi
    return 0
}

# 检查目录是否存在
check_directory() {
    if [ ! -d "$1" ]; then
        print_error "目录 '$1' 不存在"
        return 1
    fi
    return 0
}

# 创建目录（如果不存在）
ensure_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        print_success "创建目录: $1"
    fi
}

# 检查系统环境
check_environment() {
    print_step "检查系统环境..."

    # 检查必要的命令
    local required_commands=("node" "npm" "python3" "git")
    local missing_commands=()

    for cmd in "${required_commands[@]}"; do
        if ! check_command $cmd; then
            missing_commands+=($cmd)
        fi
    done

    if [ ${#missing_commands[@]} -ne 0 ]; then
        print_error "缺少必要的命令: ${missing_commands[*]}"
        print_message $YELLOW "请安装以下软件："
        for cmd in "${missing_commands[@]}"; do
            case $cmd in
                "node"|"npm")
                    echo "  - Node.js (https://nodejs.org/)"
                    ;;
                "python3")
                    echo "  - Python 3.11+ (https://python.org/)"
                    ;;
                "git")
                    echo "  - Git (https://git-scm.com/)"
                    ;;
            esac
        done
        exit 1
    fi

    # 检查版本
    local node_version=$(node --version | sed 's/v//')
    local python_version=$(python3 --version | awk '{print $2}')

    print_success "Node.js: $node_version"
    print_success "Python: $python_version"

    # 检查项目结构
    if ! check_directory ".kiro/steering"; then
        print_error "项目结构不完整，请确保在正确的项目根目录下运行此脚本"
        exit 1
    fi

    print_success "环境检查通过"
}

# 安装 Node.js 依赖
install_node_dependencies() {
    print_step "安装 Node.js 依赖..."

    # 检查 package.json 是否存在
    if [ ! -f "package.json" ]; then
        print_step "创建 package.json..."
        cat > package.json << 'EOF'
{
  "name": "cet4-learning-system",
  "version": "1.0.0",
  "description": "英语四级学习系统",
  "scripts": {
    "cursor:setup": "bash scripts/setup-cursor-rules.sh",
    "cursor:update": "node scripts/cursor-docs-helper.js --update",
    "cursor:status": "node scripts/cursor-docs-helper.js --status",
    "dev:backend": "cd app && python main.py",
    "dev:frontend": "cd frontend && npm run dev",
    "quality:check": "npm run lint && npm run type-check",
    "lint": "cd frontend && npm run lint",
    "type-check": "cd frontend && npm run type-check"
  },
  "devDependencies": {
    "chokidar": "^3.5.3",
    "nodemon": "^3.0.1"
  }
}
EOF
        print_success "创建 package.json"
    fi

    # 安装依赖
    if [ -f "package.json" ]; then
        npm install
        print_success "Node.js 依赖安装完成"
    fi

    # 安装前端依赖
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        print_step "安装前端依赖..."
        cd frontend
        npm install
        cd ..
        print_success "前端依赖安装完成"
    fi
}

# 创建目录结构
create_directory_structure() {
    print_step "创建目录结构..."

    # 创建必要的目录
    local directories=(
        ".cursor"
        ".vscode"
        "scripts"
        "logs"
        ".cursor/templates"
    )

    for dir in "${directories[@]}"; do
        ensure_directory "$dir"
    done

    print_success "目录结构创建完成"
}

# 生成规则文件
generate_rules_files() {
    print_step "生成 Cursor 规则文件..."

    # 检查文档助手脚本是否存在
    if [ ! -f "scripts/cursor-docs-helper.js" ]; then
        print_error "文档助手脚本不存在: scripts/cursor-docs-helper.js"
        exit 1
    fi

    # 运行文档助手脚本
    node scripts/cursor-docs-helper.js --update

    print_success "规则文件生成完成"
}

# 配置 Git 忽略文件
configure_gitignore() {
    print_step "配置 .gitignore..."

    # 添加 Cursor 相关的忽略规则
    local cursor_ignores=(
        "# Cursor IDE"
        ".cursor/cache/"
        ".cursor/logs/"
        ".cursor/temp/"
        ""
        "# 开发环境"
        ".env.local"
        ".env.development"
        "logs/"
        "*.log"
        ""
        "# Python"
        "__pycache__/"
        "*.pyc"
        "*.pyo"
        "*.pyd"
        ".Python"
        "build/"
        "develop-eggs/"
        "dist/"
        "downloads/"
        "eggs/"
        ".eggs/"
        "lib/"
        "lib64/"
        "parts/"
        "sdist/"
        "var/"
        "wheels/"
        "*.egg-info/"
        ".installed.cfg"
        "*.egg"
        ""
        "# Node.js"
        "node_modules/"
        "npm-debug.log*"
        "yarn-debug.log*"
        "yarn-error.log*"
    )

    # 检查 .gitignore 是否存在
    if [ ! -f ".gitignore" ]; then
        touch .gitignore
    fi

    # 添加忽略规则（如果不存在）
    for ignore in "${cursor_ignores[@]}"; do
        if [ -n "$ignore" ] && ! grep -Fxq "$ignore" .gitignore; then
            echo "$ignore" >> .gitignore
        fi
    done

    print_success ".gitignore 配置完成"
}

# 创建快速启动脚本
create_quick_start_scripts() {
    print_step "创建快速启动脚本..."

    # 创建开发环境启动脚本
    cat > scripts/dev-start.sh << 'EOF'
#!/bin/bash

# 快速启动开发环境

echo "🚀 启动英语四级学习系统开发环境..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 启动数据库服务
echo "📊 启动数据库服务..."
docker-compose up -d postgres redis milvus minio

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo "✅ 开发环境启动完成！"
echo ""
echo "📝 接下来可以："
echo "  1. 启动后端: python app/main.py"
echo "  2. 启动前端: cd frontend && npm run dev"
echo "  3. 访问应用: http://localhost:3000"
echo ""
EOF

    chmod +x scripts/dev-start.sh

    # 创建质量检查脚本
    cat > scripts/quality-check.sh << 'EOF'
#!/bin/bash

# 代码质量检查脚本

echo "🔍 开始代码质量检查..."

# Python 质量检查
echo "📋 Python 代码检查..."
if command -v ruff &> /dev/null; then
    ruff check . --output-format=github
else
    echo "⚠️  Ruff 未安装，跳过 Python 检查"
fi

if command -v mypy &> /dev/null; then
    mypy . --strict
else
    echo "⚠️  MyPy 未安装，跳过类型检查"
fi

# TypeScript 质量检查
if [ -d "frontend" ]; then
    echo "📋 TypeScript 代码检查..."
    cd frontend
    if [ -f "package.json" ]; then
        npm run lint
        npm run type-check
    fi
    cd ..
fi

echo "✅ 质量检查完成！"
EOF

    chmod +x scripts/quality-check.sh

    print_success "快速启动脚本创建完成"
}

# 创建 Cursor 使用指南
create_cursor_guide() {
    print_step "创建 Cursor 使用指南..."

    cat > .cursor/CURSOR_GUIDE.md << 'EOF'
# Cursor IDE 使用指南

## 🎯 快速开始

### 1. 基本配置
- 主规则文件：`.cursorrules` (核心架构规则)
- 详细规则：`.cursor/rules-*.md` (分类专业规则)
- 快速参考：`.cursor/quick-reference.md`

### 2. 常用命令

#### 在 Cursor Chat 中使用：
```
# 检查文件位置
根据模块化规则，这个用户认证文件应该放在哪里？

# AI服务集成检查
读取 .cursor/rules-ai.md 并检查这个DeepSeek API调用

# 教育系统合规检查
参考 .cursor/rules-education.md 验证这个学生数据处理逻辑

# 性能优化分析
根据 .cursor/rules-performance.md 分析这段代码的性能
```

### 3. 文件创建最佳实践

#### ✅ 正确方式：
```
在 app/users/api/v1/ 目录下创建 auth_endpoints.py 文件，
实现JWT认证和权限验证的API端点，
请严格遵循单体架构模块化设计原则
```

#### ❌ 错误方式：
```
创建一个用户管理的API文件
```

### 4. 代码Review工作流

1. **编写代码时**：Cursor 会根据 `.cursorrules` 自动提示
2. **保存文件时**：自动运行代码格式化和基础检查
3. **提交前**：使用 Chat 进行深度分析
4. **部署前**：运行完整的质量检查

### 5. 快捷键和命令

- `Cmd+Shift+P` → "Cursor: Chat" → 打开AI对话
- `Cmd+K` → 快速AI编辑
- `Cmd+L` → 选择代码并询问AI
- `Cmd+I` → 在光标位置插入AI生成的代码

### 6. 规则文件更新

```bash
# 更新规则文件
npm run cursor:update

# 检查规则状态
npm run cursor:status

# 手动更新
node scripts/cursor-docs-helper.js --update
```

### 7. 故障排除

#### 规则文件不生效
1. 重启 Cursor IDE
2. 检查 `.cursorrules` 文件格式
3. 运行 `npm run cursor:status` 检查状态

#### AI响应慢或不准确
1. 检查规则文件大小（应 < 10KB）
2. 简化提示内容
3. 使用具体的规则文件引用

#### 代码提示不准确
1. 确保在正确的模块目录下
2. 检查文件命名是否符合规范
3. 使用明确的业务领域关键词

## 📚 学习资源

- [Cursor 官方文档](https://cursor.sh/docs)
- [项目架构文档](.kiro/specs/cet4-learning-system/design.md)
- [开发规范文档](.kiro/steering/)

## 🆘 获取帮助

遇到问题时：
1. 查看 `.cursor/quick-reference.md`
2. 运行 `node scripts/cursor-docs-helper.js --help`
3. 检查项目文档 `.kiro/` 目录
EOF

    print_success "Cursor 使用指南创建完成"
}

# 验证安装
verify_installation() {
    print_step "验证安装..."

    local errors=0

    # 检查关键文件
    local required_files=(
        ".cursorrules"
        ".cursor/rules-ai.md"
        ".cursor/rules-education.md"
        ".cursor/rules-performance.md"
        ".cursor/rules-security.md"
        ".vscode/settings.json"
        "scripts/cursor-docs-helper.js"
    )

    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            local size=$(du -h "$file" | cut -f1)
            print_success "$file ($size)"
        else
            print_error "缺少文件: $file"
            ((errors++))
        fi
    done

    # 检查脚本可执行性
    if [ -f "scripts/cursor-docs-helper.js" ]; then
        if node scripts/cursor-docs-helper.js --status > /dev/null 2>&1; then
            print_success "文档助手脚本运行正常"
        else
            print_error "文档助手脚本运行失败"
            ((errors++))
        fi
    fi

    if [ $errors -eq 0 ]; then
        print_success "安装验证通过！"
        return 0
    else
        print_error "发现 $errors 个问题，请检查并修复"
        return 1
    fi
}

# 显示完成信息
show_completion_info() {
    print_header "🎉 Cursor 规则配置完成！"

    echo "📋 已创建的文件："
    echo "  ├── .cursorrules (主规则文件)"
    echo "  ├── .cursor/"
    echo "  │   ├── rules-ai.md (AI服务规则)"
    echo "  │   ├── rules-education.md (教育系统规则)"
    echo "  │   ├── rules-performance.md (性能优化规则)"
    echo "  │   ├── rules-security.md (安全规范)"
    echo "  │   ├── quick-reference.md (快速参考)"
    echo "  │   └── CURSOR_GUIDE.md (使用指南)"
    echo "  ├── .vscode/"
    echo "  │   ├── settings.json (工作区配置)"
    echo "  │   ├── tasks.json (任务配置)"
    echo "  │   └── launch.json (调试配置)"
    echo "  └── scripts/"
    echo "      ├── cursor-docs-helper.js (文档助手)"
    echo "      ├── dev-start.sh (开发环境启动)"
    echo "      └── quality-check.sh (质量检查)"
    echo

    print_message $CYAN "🚀 下一步操作："
    echo "  1. 重启 Cursor IDE 以加载新配置"
    echo "  2. 打开 .cursor/CURSOR_GUIDE.md 查看使用指南"
    echo "  3. 在 Cursor Chat 中测试规则："
    echo "     '根据模块化规则，用户认证文件应该放在哪里？'"
    echo "  4. 开始开发："
    echo "     bash scripts/dev-start.sh"
    echo

    print_message $GREEN "✨ 享受智能化的开发体验！"
}

# 主函数
main() {
    print_header "$PROJECT_NAME - Cursor 规则自动化设置"
    print_message $PURPLE "版本: $VERSION"
    echo

    # 检查是否在项目根目录
    if [ ! -f ".cursorrules" ] && [ ! -d ".kiro" ]; then
        print_error "请在项目根目录下运行此脚本"
        exit 1
    fi

    # 执行安装步骤
    check_environment
    install_node_dependencies
    create_directory_structure
    generate_rules_files
    configure_gitignore
    create_quick_start_scripts
    create_cursor_guide

    # 验证安装
    if verify_installation; then
        show_completion_info
        exit 0
    else
        print_error "安装过程中出现问题，请检查错误信息"
        exit 1
    fi
}

# 处理命令行参数
case "${1:-}" in
    --help|-h)
        echo "用法: $0 [选项]"
        echo
        echo "选项:"
        echo "  --help, -h     显示帮助信息"
        echo "  --verify       仅验证安装"
        echo "  --update       仅更新规则文件"
        echo
        echo "示例:"
        echo "  $0              # 完整安装"
        echo "  $0 --verify     # 验证安装"
        echo "  $0 --update     # 更新规则"
        exit 0
        ;;
    --verify)
        verify_installation
        exit $?
        ;;
    --update)
        if [ -f "scripts/cursor-docs-helper.js" ]; then
            node scripts/cursor-docs-helper.js --update
        else
            print_error "文档助手脚本不存在"
            exit 1
        fi
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "未知选项: $1"
        echo "使用 --help 查看帮助信息"
        exit 1
        ;;
esac
