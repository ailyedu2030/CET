#!/bin/bash
# CET4学习系统 - 本地代码质量检查脚本
# 在提交前运行完整的质量检查

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

log_info "开始CET4学习系统代码质量检查..."

# 创建报告目录
REPORT_DIR="quality-reports"
mkdir -p "$REPORT_DIR"

# 1. Python依赖检查
log_info "检查Python依赖..."
if ! python -c "import httpx, aiofiles; from jose import jwt" 2>/dev/null; then
    log_warning "缺少必需的依赖，正在安装..."
    pip install httpx aiofiles 'python-jose[cryptography]'
fi
log_success "Python依赖检查完成"

# 2. Ruff代码检查
log_info "运行Ruff代码检查..."
# 只检查Python文件，避免检查JSON等配置文件
if ruff check app/ --output-format=json > "$REPORT_DIR/ruff-report.json"; then
    log_success "Ruff检查通过"
else
    log_error "Ruff检查发现问题，查看 $REPORT_DIR/ruff-report.json"
    ruff check app/ --output-format=github
fi

# 3. 代码格式化检查
log_info "检查代码格式化..."
if ruff format --check app/; then
    log_success "代码格式化正确"
else
    log_warning "代码格式不正确，运行 'ruff format app/' 进行修复"
fi

# 4. MyPy类型检查
log_info "运行MyPy类型检查..."
if mypy app/ --ignore-missing-imports --show-error-codes > "$REPORT_DIR/mypy-report.txt" 2>&1; then
    log_success "MyPy类型检查通过"
else
    log_error "MyPy类型检查发现问题，查看 $REPORT_DIR/mypy-report.txt"
    cat "$REPORT_DIR/mypy-report.txt"
fi

# 5. 安全扫描
log_info "运行安全扫描..."
if command -v bandit >/dev/null 2>&1; then
    if bandit -r app/ -f json -o "$REPORT_DIR/bandit-report.json" -ll; then
        log_success "Bandit安全扫描通过"
    else
        log_warning "Bandit发现安全问题，查看 $REPORT_DIR/bandit-report.json"
    fi
else
    log_warning "Bandit未安装，跳过安全扫描"
fi

# 6. 依赖安全检查
log_info "检查依赖安全..."
if command -v safety >/dev/null 2>&1; then
    if safety check --json --output "$REPORT_DIR/safety-report.json"; then
        log_success "依赖安全检查通过"
    else
        log_warning "发现依赖安全问题，查看 $REPORT_DIR/safety-report.json"
    fi
else
    log_warning "Safety未安装，跳过依赖安全检查"
fi

# 7. 代码复杂度检查
log_info "检查代码复杂度..."
if command -v radon >/dev/null 2>&1; then
    radon cc app/ -a -nc > "$REPORT_DIR/complexity-report.txt"
    radon mi app/ -nc > "$REPORT_DIR/maintainability-report.txt"
    log_success "代码复杂度检查完成"
else
    log_warning "Radon未安装，跳过复杂度检查"
fi

# 8. 死代码检测
log_info "检测死代码..."
if command -v vulture >/dev/null 2>&1; then
    vulture app/ --min-confidence 80 --sort-by-size > "$REPORT_DIR/vulture-report.txt" || true
    log_success "死代码检测完成"
else
    log_warning "Vulture未安装，跳过死代码检测"
fi

# 9. 测试运行
log_info "运行测试..."
if [ -d "tests" ]; then
    if pytest tests/ -v --cov=app --cov-report=html:"$REPORT_DIR/coverage-html" --cov-report=json:"$REPORT_DIR/coverage.json" > "$REPORT_DIR/test-report.txt" 2>&1; then
        log_success "测试通过"
    else
        log_error "测试失败，查看 $REPORT_DIR/test-report.txt"
    fi
else
    log_warning "未找到tests目录，跳过测试"
fi

# 10. 前端检查（如果存在）
if [ -d "frontend" ]; then
    log_info "检查前端代码..."
    cd frontend
    
    if [ -f "package.json" ]; then
        # 安装依赖
        if [ ! -d "node_modules" ]; then
            log_info "安装前端依赖..."
            npm ci
        fi
        
        # ESLint检查
        if npm run lint > "../$REPORT_DIR/eslint-report.txt" 2>&1; then
            log_success "ESLint检查通过"
        else
            log_warning "ESLint发现问题，查看 $REPORT_DIR/eslint-report.txt"
        fi
        
        # TypeScript检查
        if npm run type-check > "../$REPORT_DIR/typescript-report.txt" 2>&1; then
            log_success "TypeScript检查通过"
        else
            log_warning "TypeScript检查发现问题，查看 $REPORT_DIR/typescript-report.txt"
        fi
        
        # 前端测试
        if npm test > "../$REPORT_DIR/frontend-test-report.txt" 2>&1; then
            log_success "前端测试通过"
        else
            log_warning "前端测试失败，查看 $REPORT_DIR/frontend-test-report.txt"
        fi
    fi
    
    cd ..
fi

# 11. 生成质量报告
log_info "生成质量报告..."
if [ -f ".github/scripts/quality-report.py" ]; then
    python .github/scripts/quality-report.py "$REPORT_DIR" "$REPORT_DIR/quality-report.md"
    log_success "质量报告已生成: $REPORT_DIR/quality-report.md"
else
    log_warning "质量报告生成器未找到"
fi

# 12. 总结
log_info "质量检查完成！"
echo ""
echo "📊 报告文件位置:"
echo "  - 详细报告: $REPORT_DIR/"
echo "  - 质量总结: $REPORT_DIR/quality-report.md"
echo ""

# 检查是否有严重问题
CRITICAL_ISSUES=0

if [ -f "$REPORT_DIR/ruff-report.json" ] && [ -s "$REPORT_DIR/ruff-report.json" ]; then
    RUFF_ISSUES=$(jq length "$REPORT_DIR/ruff-report.json" 2>/dev/null || echo "0")
    if [ "$RUFF_ISSUES" -gt 0 ]; then
        CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
    fi
fi

if [ -f "$REPORT_DIR/bandit-report.json" ]; then
    HIGH_SECURITY=$(jq '.results[] | select(.issue_severity == "HIGH") | length' "$REPORT_DIR/bandit-report.json" 2>/dev/null | wc -l || echo "0")
    if [ "$HIGH_SECURITY" -gt 0 ]; then
        CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
    fi
fi

if [ "$CRITICAL_ISSUES" -gt 0 ]; then
    log_error "发现 $CRITICAL_ISSUES 个严重问题，请修复后再提交"
    exit 1
else
    log_success "所有质量检查通过！代码可以提交 🚀"
fi
