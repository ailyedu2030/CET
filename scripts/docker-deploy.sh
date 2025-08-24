#!/bin/bash

# 英语四级学习系统 - Docker部署脚本
# 用于部署和管理Docker容器服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="cet4-learning"
COMPOSE_FILE="docker-compose.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

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
    log_info "检查部署环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查配置文件
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose配置文件不存在: $COMPOSE_FILE"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 创建环境变量文件
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_info "创建环境变量文件..."
        
        cat > "$ENV_FILE" << EOF
# 英语四级学习系统环境变量配置

# 数据库配置
POSTGRES_PASSWORD=cet4_password_2024_secure
POSTGRES_DB=cet4_learning
POSTGRES_USER=cet4_user

# Redis配置
REDIS_PASSWORD=cet4_redis_2024_secure

# MinIO配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123secure

# 应用配置
SECRET_KEY=cet4-learning-secret-key-2024-very-secure-change-in-production
DEBUG=false
ENVIRONMENT=production

# AI服务配置（请替换为实际的API密钥）
DEEPSEEK_API_KEYS=sk-xxx,sk-yyy,sk-zzz

# 域名配置
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ORIGINS=http://localhost,https://your-domain.com

# 监控配置
GRAFANA_PASSWORD=admin123secure
EOF
        
        log_warning "请编辑 $ENV_FILE 文件，设置正确的环境变量值"
        log_warning "特别是 DEEPSEEK_API_KEYS 和密码相关配置"
    else
        log_info "环境变量文件已存在: $ENV_FILE"
    fi
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 等待数据库启动
    log_info "等待PostgreSQL启动..."
    docker-compose exec postgres sh -c 'until pg_isready -U $POSTGRES_USER -d $POSTGRES_DB; do sleep 1; done'
    
    # 运行数据库迁移
    log_info "运行数据库迁移..."
    docker-compose exec app alembic upgrade head
    
    log_success "数据库初始化完成"
}

# 启动服务
start_services() {
    local ENVIRONMENT=${1:-development}
    
    log_info "启动服务 (环境: $ENVIRONMENT)..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f "$COMPOSE_FILE" -f "$PROD_COMPOSE_FILE" up -d
    else
        docker-compose up -d
    fi
    
    log_success "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    local ENVIRONMENT=${1:-development}
    
    log_info "重启服务..."
    stop_services
    start_services "$ENVIRONMENT"
    log_success "服务重启完成"
}

# 查看服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
    
    echo ""
    log_info "服务健康状态:"
    docker-compose exec app curl -f http://localhost:8000/health || log_warning "应用健康检查失败"
    docker-compose exec postgres pg_isready -U cet4_user -d cet4_learning || log_warning "数据库健康检查失败"
    docker-compose exec redis redis-cli ping || log_warning "Redis健康检查失败"
}

# 查看日志
show_logs() {
    local SERVICE=${1:-}
    local LINES=${2:-100}
    
    if [ -z "$SERVICE" ]; then
        log_info "显示所有服务日志 (最近 $LINES 行):"
        docker-compose logs --tail="$LINES" -f
    else
        log_info "显示 $SERVICE 服务日志 (最近 $LINES 行):"
        docker-compose logs --tail="$LINES" -f "$SERVICE"
    fi
}

# 备份数据
backup_data() {
    local BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "创建数据备份..."
    mkdir -p "$BACKUP_DIR"
    
    # 备份数据库
    log_info "备份PostgreSQL数据库..."
    docker-compose exec postgres pg_dump -U cet4_user cet4_learning > "$BACKUP_DIR/postgres_backup.sql"
    
    # 备份Redis数据
    log_info "备份Redis数据..."
    docker-compose exec redis redis-cli --rdb - > "$BACKUP_DIR/redis_backup.rdb"
    
    # 备份上传文件
    log_info "备份上传文件..."
    docker cp $(docker-compose ps -q app):/app/uploads "$BACKUP_DIR/uploads" 2>/dev/null || true
    
    # 备份报表文件
    log_info "备份报表文件..."
    docker cp $(docker-compose ps -q app):/app/reports "$BACKUP_DIR/reports" 2>/dev/null || true
    
    # 创建备份信息文件
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
备份时间: $(date)
项目名称: $PROJECT_NAME
备份内容:
- PostgreSQL数据库
- Redis数据
- 上传文件
- 报表文件
EOF
    
    log_success "数据备份完成: $BACKUP_DIR"
}

# 更新服务
update_services() {
    local ENVIRONMENT=${1:-development}
    
    log_info "更新服务..."
    
    # 备份数据
    backup_data
    
    # 拉取最新镜像
    log_info "拉取最新镜像..."
    docker-compose pull
    
    # 重新构建应用镜像
    log_info "重新构建应用镜像..."
    docker-compose build --no-cache app
    
    # 重启服务
    restart_services "$ENVIRONMENT"
    
    # 运行数据库迁移
    init_database
    
    log_success "服务更新完成"
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 停止并删除容器
    docker-compose down --volumes --remove-orphans
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的卷
    docker volume prune -f
    
    # 清理未使用的网络
    docker network prune -f
    
    log_success "资源清理完成"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  start [env]     启动服务 (env: development|production)"
    echo "  stop            停止服务"
    echo "  restart [env]   重启服务"
    echo "  status          查看服务状态"
    echo "  logs [service]  查看日志"
    echo "  backup          备份数据"
    echo "  update [env]    更新服务"
    echo "  cleanup         清理资源"
    echo "  init            初始化部署环境"
    echo ""
    echo "示例:"
    echo "  $0 init                    # 初始化部署环境"
    echo "  $0 start                   # 启动开发环境"
    echo "  $0 start production        # 启动生产环境"
    echo "  $0 logs app                # 查看应用日志"
    echo "  $0 backup                  # 备份数据"
}

# 初始化部署环境
init_deployment() {
    log_info "初始化部署环境..."
    
    # 检查环境
    check_environment
    
    # 创建环境变量文件
    create_env_file
    
    # 创建必要的目录
    mkdir -p backups logs uploads reports
    
    # 设置脚本权限
    chmod +x scripts/*.sh
    
    log_success "部署环境初始化完成"
    log_info "请编辑 $ENV_FILE 文件，然后运行: $0 start"
}

# 主函数
main() {
    case "${1:-}" in
        start)
            check_environment
            start_services "${2:-development}"
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_environment
            restart_services "${2:-development}"
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-}" "${3:-100}"
            ;;
        backup)
            backup_data
            ;;
        update)
            update_services "${2:-development}"
            ;;
        cleanup)
            cleanup
            ;;
        init)
            init_deployment
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            log_error "未知命令: ${1:-}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
