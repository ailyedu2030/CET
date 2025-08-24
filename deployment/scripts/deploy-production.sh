#!/bin/bash

# 英语四级学习系统 - 生产环境部署脚本
# 用于自动化部署到生产环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment/production"
BACKUP_DIR="/opt/cet4-learning/backups"
LOG_FILE="/var/log/cet4-deployment.log"

# 默认配置
IMAGE_TAG=${IMAGE_TAG:-latest}
ENVIRONMENT=${ENVIRONMENT:-production}
FORCE_DEPLOY=${FORCE_DEPLOY:-false}
SKIP_BACKUP=${SKIP_BACKUP:-false}
SKIP_TESTS=${SKIP_TESTS:-false}

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
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
    
    # 检查必要的目录
    if [ ! -d "$DEPLOYMENT_DIR" ]; then
        log_error "部署目录不存在: $DEPLOYMENT_DIR"
        exit 1
    fi
    
    # 检查环境变量文件
    if [ ! -f "$DEPLOYMENT_DIR/env.prod" ]; then
        log_error "生产环境变量文件不存在: $DEPLOYMENT_DIR/env.prod"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 检查系统资源
check_system_resources() {
    log_info "检查系统资源..."
    
    # 检查磁盘空间
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 85 ]; then
        log_error "磁盘空间不足，使用率: ${DISK_USAGE}%"
        exit 1
    fi
    
    # 检查内存
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$MEMORY_USAGE" -gt 90 ]; then
        log_warning "内存使用率较高: ${MEMORY_USAGE}%"
    fi
    
    log_success "系统资源检查通过"
}

# 备份当前部署
backup_current_deployment() {
    if [ "$SKIP_BACKUP" = "true" ]; then
        log_info "跳过备份"
        return 0
    fi
    
    log_info "备份当前部署..."
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    # 创建备份目录
    mkdir -p "$BACKUP_PATH"
    
    # 备份Docker Compose文件
    if [ -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" ]; then
        cp "$DEPLOYMENT_DIR/docker-compose.prod.yml" "$BACKUP_PATH/"
    fi
    
    # 备份环境变量文件
    if [ -f "$DEPLOYMENT_DIR/.env" ]; then
        cp "$DEPLOYMENT_DIR/.env" "$BACKUP_PATH/"
    fi
    
    # 备份数据库
    log_info "备份数据库..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" exec -T postgres \
        pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_PATH/database_backup.sql" || true
    
    # 备份Redis数据
    log_info "备份Redis数据..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" exec -T redis \
        redis-cli --rdb - > "$BACKUP_PATH/redis_backup.rdb" || true
    
    # 记录当前镜像版本
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" \
        > "$BACKUP_PATH/images.txt"
    
    echo "$BACKUP_PATH" > "$DEPLOYMENT_DIR/.last_backup"
    
    log_success "备份完成: $BACKUP_PATH"
}

# 拉取最新镜像
pull_latest_images() {
    log_info "拉取最新镜像..."
    
    cd "$DEPLOYMENT_DIR"
    
    # 设置镜像标签
    export IMAGE_TAG="$IMAGE_TAG"
    
    # 拉取镜像
    docker-compose -f docker-compose.prod.yml pull
    
    log_success "镜像拉取完成"
}

# 运行预部署测试
run_pre_deployment_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_info "跳过预部署测试"
        return 0
    fi
    
    log_info "运行预部署测试..."
    
    # 检查镜像是否存在
    if ! docker images | grep -q "cet4-learning.*$IMAGE_TAG"; then
        log_error "镜像不存在: cet4-learning:$IMAGE_TAG"
        exit 1
    fi
    
    # 运行容器健康检查
    log_info "测试容器启动..."
    docker run --rm --name cet4-test \
        -e ENVIRONMENT=test \
        -e DEBUG=false \
        ghcr.io/your-org/cet4-learning:$IMAGE_TAG \
        python -c "print('Container test passed')" || {
        log_error "容器测试失败"
        exit 1
    }
    
    log_success "预部署测试通过"
}

# 部署服务
deploy_services() {
    log_info "部署服务..."
    
    cd "$DEPLOYMENT_DIR"
    
    # 复制环境变量文件
    cp env.prod .env
    
    # 设置镜像标签
    export IMAGE_TAG="$IMAGE_TAG"
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans || true
    
    # 启动新服务
    log_info "启动新服务..."
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "服务部署完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "应用服务就绪"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 10
    done
    
    log_error "服务启动超时"
    return 1
}

# 运行健康检查
run_health_checks() {
    log_info "运行健康检查..."
    
    local checks_passed=0
    local total_checks=5
    
    # 检查应用健康状态
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "✅ 应用健康检查通过"
        checks_passed=$((checks_passed + 1))
    else
        log_error "❌ 应用健康检查失败"
    fi
    
    # 检查数据库连接
    if docker-compose -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" exec -T app \
        python -c "
import asyncio
from app.core.database import get_database
async def test_db():
    try:
        db = get_database()
        await db.execute('SELECT 1')
        print('Database OK')
    except Exception as e:
        print(f'Database Error: {e}')
        exit(1)
asyncio.run(test_db())
        " >/dev/null 2>&1; then
        log_success "✅ 数据库连接检查通过"
        checks_passed=$((checks_passed + 1))
    else
        log_error "❌ 数据库连接检查失败"
    fi
    
    # 检查Redis连接
    if docker-compose -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" exec -T redis \
        redis-cli ping >/dev/null 2>&1; then
        log_success "✅ Redis连接检查通过"
        checks_passed=$((checks_passed + 1))
    else
        log_error "❌ Redis连接检查失败"
    fi
    
    # 检查Nginx状态
    if curl -f http://localhost/ >/dev/null 2>&1; then
        log_success "✅ Nginx健康检查通过"
        checks_passed=$((checks_passed + 1))
    else
        log_error "❌ Nginx健康检查失败"
    fi
    
    # 检查容器状态
    local unhealthy_containers=$(docker-compose -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" \
        ps --filter "health=unhealthy" -q | wc -l)
    if [ "$unhealthy_containers" -eq 0 ]; then
        log_success "✅ 所有容器健康状态正常"
        checks_passed=$((checks_passed + 1))
    else
        log_error "❌ 发现 $unhealthy_containers 个不健康的容器"
    fi
    
    # 评估健康检查结果
    if [ $checks_passed -eq $total_checks ]; then
        log_success "所有健康检查通过 ($checks_passed/$total_checks)"
        return 0
    elif [ $checks_passed -ge 3 ]; then
        log_warning "部分健康检查通过 ($checks_passed/$total_checks)"
        return 0
    else
        log_error "健康检查失败 ($checks_passed/$total_checks)"
        return 1
    fi
}

# 回滚部署
rollback_deployment() {
    log_warning "开始回滚部署..."
    
    if [ ! -f "$DEPLOYMENT_DIR/.last_backup" ]; then
        log_error "未找到备份信息，无法回滚"
        return 1
    fi
    
    local backup_path=$(cat "$DEPLOYMENT_DIR/.last_backup")
    
    if [ ! -d "$backup_path" ]; then
        log_error "备份目录不存在: $backup_path"
        return 1
    fi
    
    # 停止当前服务
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" down --remove-orphans
    
    # 恢复配置文件
    if [ -f "$backup_path/docker-compose.prod.yml" ]; then
        cp "$backup_path/docker-compose.prod.yml" "$DEPLOYMENT_DIR/"
    fi
    
    if [ -f "$backup_path/.env" ]; then
        cp "$backup_path/.env" "$DEPLOYMENT_DIR/"
    fi
    
    # 启动服务
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.prod.yml" up -d
    
    # 等待服务就绪
    if wait_for_services; then
        log_success "回滚完成"
        return 0
    else
        log_error "回滚失败"
        return 1
    fi
}

# 清理旧资源
cleanup_old_resources() {
    log_info "清理旧资源..."
    
    # 清理旧镜像
    docker image prune -f
    
    # 清理旧容器
    docker container prune -f
    
    # 清理旧网络
    docker network prune -f
    
    # 清理旧备份（保留最近10个）
    if [ -d "$BACKUP_DIR" ]; then
        ls -t "$BACKUP_DIR"/backup_* 2>/dev/null | tail -n +11 | xargs rm -rf 2>/dev/null || true
    fi
    
    log_success "资源清理完成"
}

# 发送部署通知
send_deployment_notification() {
    local status=$1
    local message=$2
    
    log_info "发送部署通知..."
    
    # Slack通知
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 生产环境部署通知\\n环境: $ENVIRONMENT\\n状态: $status\\n消息: $message\\n时间: $(date)\\n镜像: $IMAGE_TAG\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi
    
    log_success "部署通知已发送"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示帮助信息"
    echo "  --image-tag TAG         指定镜像标签 (默认: latest)"
    echo "  --force                 强制部署，跳过确认"
    echo "  --skip-backup           跳过备份"
    echo "  --skip-tests            跳过预部署测试"
    echo "  --rollback              回滚到上一个版本"
    echo ""
    echo "环境变量:"
    echo "  IMAGE_TAG               镜像标签"
    echo "  FORCE_DEPLOY            强制部署"
    echo "  SKIP_BACKUP             跳过备份"
    echo "  SKIP_TESTS              跳过测试"
    echo "  SLACK_WEBHOOK_URL       Slack通知URL"
}

# 主函数
main() {
    local ROLLBACK=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --image-tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_info "开始生产环境部署..."
    log_info "镜像标签: $IMAGE_TAG"
    log_info "环境: $ENVIRONMENT"
    
    # 处理回滚
    if [ "$ROLLBACK" = "true" ]; then
        if rollback_deployment; then
            send_deployment_notification "回滚成功" "成功回滚到上一个版本"
            log_success "回滚完成！"
        else
            send_deployment_notification "回滚失败" "回滚过程中出现错误"
            log_error "回滚失败"
            exit 1
        fi
        return 0
    fi
    
    # 确认部署
    if [ "$FORCE_DEPLOY" != "true" ]; then
        echo -n "确认部署到生产环境？(y/N): "
        read -r confirmation
        if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
            log_info "部署已取消"
            exit 0
        fi
    fi
    
    # 执行部署流程
    check_dependencies
    check_system_resources
    backup_current_deployment
    pull_latest_images
    run_pre_deployment_tests
    deploy_services
    
    if wait_for_services && run_health_checks; then
        cleanup_old_resources
        send_deployment_notification "成功" "生产环境部署成功完成"
        log_success "生产环境部署成功完成！"
    else
        log_error "部署失败，尝试回滚..."
        if rollback_deployment; then
            send_deployment_notification "回滚成功" "部署失败，已成功回滚"
            log_warning "部署失败，已回滚到之前版本"
            exit 1
        else
            send_deployment_notification "失败" "部署失败，回滚也失败"
            log_error "部署失败，回滚也失败"
            exit 1
        fi
    fi
}

# 执行主函数
main "$@"
