#!/bin/bash

# 英语四级学习系统 - 自动化测试脚本
# 用于CI/CD流水线中的测试执行

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PYTHON_VERSION=${PYTHON_VERSION:-3.11}
NODE_VERSION=${NODE_VERSION:-18}
TEST_ENV=${TEST_ENV:-test}
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-80}

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_environment() {
    log_info "检查测试环境..."
    
    # 检查Python版本
    if ! python --version | grep -q "$PYTHON_VERSION"; then
        log_error "Python版本不匹配，期望: $PYTHON_VERSION"
        exit 1
    fi
    
    # 检查Node.js版本
    if ! node --version | grep -q "v$NODE_VERSION"; then
        log_error "Node.js版本不匹配，期望: $NODE_VERSION"
        exit 1
    fi
    
    # 检查必要的环境变量
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL环境变量未设置"
        exit 1
    fi
    
    if [ -z "$REDIS_URL" ]; then
        log_error "REDIS_URL环境变量未设置"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 设置测试环境
setup_test_environment() {
    log_info "设置测试环境..."
    
    # 创建测试配置文件
    cat > .env.test << EOF
# 测试环境配置
ENVIRONMENT=test
DEBUG=true
SECRET_KEY=test-secret-key-not-for-production
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
MILVUS_HOST=localhost
MILVUS_PORT=19530
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
DEEPSEEK_API_KEYS=test-key-1,test-key-2
LOG_LEVEL=DEBUG
EOF
    
    # 设置环境变量
    export ENVIRONMENT=test
    export PYTHONPATH=$(pwd)
    
    log_success "测试环境设置完成"
}

# 安装依赖
install_dependencies() {
    log_info "安装测试依赖..."
    
    # 安装Python依赖
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-asyncio pytest-mock httpx faker
    
    # 安装前端依赖
    if [ -d "frontend" ]; then
        cd frontend
        npm ci
        cd ..
    fi
    
    log_success "依赖安装完成"
}

# 数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    # 等待数据库就绪
    log_info "等待数据库连接..."
    for i in {1..30}; do
        if python -c "
import asyncio
import asyncpg
async def test_db():
    try:
        conn = await asyncpg.connect('$DATABASE_URL')
        await conn.close()
        print('Database ready')
        exit(0)
    except Exception as e:
        print(f'Database not ready: {e}')
        exit(1)
asyncio.run(test_db())
        " 2>/dev/null; then
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "数据库连接超时"
            exit 1
        fi
        
        sleep 2
    done
    
    # 运行迁移
    alembic upgrade head
    
    log_success "数据库迁移完成"
}

# 运行后端单元测试
run_backend_tests() {
    log_info "运行后端单元测试..."
    
    # 创建测试报告目录
    mkdir -p test-reports
    
    # 运行pytest
    pytest tests/ \
        -v \
        --cov=app \
        --cov-report=xml:test-reports/coverage.xml \
        --cov-report=html:test-reports/htmlcov \
        --cov-report=term \
        --junit-xml=test-reports/pytest-report.xml \
        --tb=short
    
    # 检查覆盖率
    COVERAGE=$(python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('test-reports/coverage.xml')
root = tree.getroot()
coverage = float(root.attrib['line-rate']) * 100
print(f'{coverage:.1f}')
")
    
    log_info "测试覆盖率: ${COVERAGE}%"
    
    if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
        log_error "测试覆盖率低于阈值 ${COVERAGE_THRESHOLD}%"
        exit 1
    fi
    
    log_success "后端单元测试通过"
}

# 运行前端测试
run_frontend_tests() {
    if [ ! -d "frontend" ]; then
        log_warning "前端目录不存在，跳过前端测试"
        return 0
    fi
    
    log_info "运行前端测试..."
    
    cd frontend
    
    # 运行单元测试
    npm run test:coverage
    
    # 运行类型检查
    npm run type-check
    
    # 运行代码质量检查
    npm run lint
    
    cd ..
    
    log_success "前端测试通过"
}

# 运行集成测试
run_integration_tests() {
    log_info "运行集成测试..."
    
    # 启动测试服务
    log_info "启动测试服务..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    APP_PID=$!
    
    # 等待服务启动
    sleep 10
    
    # 运行集成测试
    pytest tests/integration/ -v --tb=short || {
        kill $APP_PID
        exit 1
    }
    
    # 停止测试服务
    kill $APP_PID
    
    log_success "集成测试通过"
}

# 运行API测试
run_api_tests() {
    log_info "运行API测试..."
    
    # 启动测试服务
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    APP_PID=$!
    
    # 等待服务启动
    sleep 10
    
    # 健康检查
    if ! curl -f http://localhost:8000/health; then
        log_error "API健康检查失败"
        kill $APP_PID
        exit 1
    fi
    
    # 运行API测试
    pytest tests/api/ -v --tb=short || {
        kill $APP_PID
        exit 1
    }
    
    # 停止测试服务
    kill $APP_PID
    
    log_success "API测试通过"
}

# 生成测试报告
generate_test_report() {
    log_info "生成测试报告..."
    
    # 创建测试报告
    cat > test-reports/test-summary.md << EOF
# 测试报告

## 测试环境
- Python版本: $(python --version)
- Node.js版本: $(node --version)
- 测试时间: $(date)

## 测试结果
- 后端单元测试: ✅ 通过
- 前端测试: ✅ 通过
- 集成测试: ✅ 通过
- API测试: ✅ 通过

## 覆盖率报告
- 后端覆盖率: ${COVERAGE}%
- 覆盖率阈值: ${COVERAGE_THRESHOLD}%

## 测试文件
- 覆盖率报告: htmlcov/index.html
- JUnit报告: pytest-report.xml
- 覆盖率XML: coverage.xml
EOF
    
    log_success "测试报告生成完成"
}

# 清理测试环境
cleanup() {
    log_info "清理测试环境..."
    
    # 停止可能运行的进程
    pkill -f "uvicorn app.main:app" || true
    
    # 清理临时文件
    rm -f .env.test
    
    log_success "清理完成"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  --unit-only         只运行单元测试"
    echo "  --integration-only  只运行集成测试"
    echo "  --api-only          只运行API测试"
    echo "  --frontend-only     只运行前端测试"
    echo "  --coverage-threshold N  设置覆盖率阈值 (默认: 80)"
    echo ""
    echo "环境变量:"
    echo "  DATABASE_URL        数据库连接URL"
    echo "  REDIS_URL          Redis连接URL"
    echo "  COVERAGE_THRESHOLD  覆盖率阈值"
}

# 主函数
main() {
    local RUN_UNIT=true
    local RUN_INTEGRATION=true
    local RUN_API=true
    local RUN_FRONTEND=true
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --unit-only)
                RUN_INTEGRATION=false
                RUN_API=false
                RUN_FRONTEND=false
                shift
                ;;
            --integration-only)
                RUN_UNIT=false
                RUN_API=false
                RUN_FRONTEND=false
                shift
                ;;
            --api-only)
                RUN_UNIT=false
                RUN_INTEGRATION=false
                RUN_FRONTEND=false
                shift
                ;;
            --frontend-only)
                RUN_UNIT=false
                RUN_INTEGRATION=false
                RUN_API=false
                shift
                ;;
            --coverage-threshold)
                COVERAGE_THRESHOLD="$2"
                shift 2
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    log_info "开始运行自动化测试..."
    
    # 执行测试流程
    check_environment
    setup_test_environment
    install_dependencies
    run_migrations
    
    if [ "$RUN_UNIT" = true ]; then
        run_backend_tests
    fi
    
    if [ "$RUN_FRONTEND" = true ]; then
        run_frontend_tests
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests
    fi
    
    if [ "$RUN_API" = true ]; then
        run_api_tests
    fi
    
    generate_test_report
    
    log_success "所有测试通过！"
}

# 执行主函数
main "$@"
