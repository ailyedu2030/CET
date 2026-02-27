#!/bin/bash

# 英语四级学习系统 - 生产环境部署脚本
# 支持本地部署到远程服务器

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器配置
SERVER_HOST="14.103.244.249"
SERVER_USER="root"
DEPLOY_DIR="/opt/cet4-learning"
PROJECT_NAME="cet4-learning"

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

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查SSH连接
    if ! ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_HOST "echo 'SSH连接正常'" &> /dev/null; then
        log_error "无法连接到服务器 $SERVER_HOST，请检查SSH配置"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 准备部署文件
prepare_deployment() {
    log_info "准备部署文件..."

    # 创建临时部署目录
    TEMP_DIR=$(mktemp -d)
    log_info "创建临时目录: $TEMP_DIR"

    # 复制项目文件（排除不需要的文件）
    cp -r . $TEMP_DIR/

    # 删除不需要的文件和目录
    rm -rf $TEMP_DIR/.git
    rm -rf $TEMP_DIR/node_modules
    find $TEMP_DIR -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find $TEMP_DIR -name "*.pyc" -type f -delete 2>/dev/null || true
    rm -rf $TEMP_DIR/.pytest_cache
    rm -rf $TEMP_DIR/logs
    rm -rf $TEMP_DIR/uploads
    rm -rf $TEMP_DIR/reports
    rm -f $TEMP_DIR/.env.local
    find $TEMP_DIR -name ".DS_Store" -type f -delete 2>/dev/null || true

    # 确保.env文件存在
    if [ ! -f "$TEMP_DIR/.env" ]; then
        log_error ".env文件不存在，请先创建环境配置文件"
        rm -rf $TEMP_DIR
        exit 1
    fi

    log_success "部署文件准备完成"
    echo $TEMP_DIR
}

# 上传文件到服务器
upload_files() {
    local temp_dir=$1
    log_info "上传文件到服务器..."
    
    # 在服务器上创建部署目录
    ssh $SERVER_USER@$SERVER_HOST "mkdir -p $DEPLOY_DIR"
    
    # 上传项目文件
    rsync -av --delete $temp_dir/ $SERVER_USER@$SERVER_HOST:$DEPLOY_DIR/
    
    log_success "文件上传完成"
}

# 服务器端部署
deploy_on_server() {
    log_info "在服务器上执行部署..."
    
    ssh $SERVER_USER@$SERVER_HOST << EOF
        set -e
        cd $DEPLOY_DIR
        
        echo "=== 停止现有服务 ==="
        docker-compose down --remove-orphans || true
        
        echo "=== 清理Docker资源 ==="
        docker system prune -f || true
        
        echo "=== 构建应用镜像 ==="
        docker-compose build --no-cache
        
        echo "=== 启动服务 ==="
        docker-compose up -d
        
        echo "=== 等待服务启动 ==="
        sleep 30
        
        echo "=== 检查服务状态 ==="
        docker-compose ps
        
        echo "=== 检查服务健康状态 ==="
        for i in {1..30}; do
            if curl -f http://localhost:8000/health &> /dev/null; then
                echo "应用服务健康检查通过"
                break
            fi
            echo "等待应用服务启动... (\$i/30)"
            sleep 10
        done
        
        echo "=== 显示服务日志 ==="
        docker-compose logs --tail=20
EOF
    
    log_success "服务器部署完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署结果..."
    
    # 检查服务状态
    ssh $SERVER_USER@$SERVER_HOST "cd $DEPLOY_DIR && docker-compose ps"
    
    # 检查应用健康状态
    if ssh $SERVER_USER@$SERVER_HOST "curl -f http://localhost:8000/health" &> /dev/null; then
        log_success "应用健康检查通过"
    else
        log_warning "应用健康检查失败，请检查日志"
    fi
    
    # 检查数据库连接
    if ssh $SERVER_USER@$SERVER_HOST "cd $DEPLOY_DIR && docker-compose exec -T app python -c 'from app.core.database import engine; print(\"数据库连接正常\")'" &> /dev/null; then
        log_success "数据库连接正常"
    else
        log_warning "数据库连接检查失败"
    fi
    
    log_success "部署验证完成"
}

# 清理临时文件
cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        log_info "清理临时文件..."
        rm -rf $TEMP_DIR
        log_success "临时文件清理完成"
    fi
}

# 主部署流程
main() {
    log_info "开始部署英语四级学习系统到生产环境"
    log_info "目标服务器: $SERVER_HOST"
    log_info "部署目录: $DEPLOY_DIR"
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    # 执行部署步骤
    check_dependencies
    TEMP_DIR=$(prepare_deployment)
    upload_files $TEMP_DIR
    deploy_on_server
    verify_deployment
    
    log_success "🎉 部署完成！"
    log_info "应用访问地址: http://$SERVER_HOST:8000"
    log_info "API文档地址: http://$SERVER_HOST:8000/docs"
    log_info "管理界面地址: http://$SERVER_HOST:8000/admin"
}

# 显示帮助信息
show_help() {
    echo "英语四级学习系统部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -v, --verify   仅验证部署状态"
    echo "  -l, --logs     查看服务日志"
    echo "  -s, --status   查看服务状态"
    echo ""
    echo "示例:"
    echo "  $0              # 执行完整部署"
    echo "  $0 --verify     # 验证部署状态"
    echo "  $0 --logs       # 查看服务日志"
}

# 查看服务日志
show_logs() {
    log_info "查看服务日志..."
    ssh $SERVER_USER@$SERVER_HOST "cd $DEPLOY_DIR && docker-compose logs --tail=50 -f"
}

# 查看服务状态
show_status() {
    log_info "查看服务状态..."
    ssh $SERVER_USER@$SERVER_HOST "cd $DEPLOY_DIR && docker-compose ps"
}

# 解析命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--verify)
        verify_deployment
        exit 0
        ;;
    -l|--logs)
        show_logs
        exit 0
        ;;
    -s|--status)
        show_status
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "未知选项: $1"
        show_help
        exit 1
        ;;
esac
