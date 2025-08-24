#!/bin/bash

# 英语四级学习系统 - 自动化部署脚本
# 用于CI/CD流水线中的部署执行

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
DEPLOYMENT_ENV=${DEPLOYMENT_ENV:-staging}
IMAGE_TAG=${IMAGE_TAG:-latest}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}
ROLLBACK_ENABLED=${ROLLBACK_ENABLED:-true}

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

# 检查部署环境
check_deployment_environment() {
    log_info "检查部署环境: $DEPLOYMENT_ENV"
    
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
    
    # 检查必要的环境变量
    case $DEPLOYMENT_ENV in
        staging)
            required_vars=(
                "STAGING_POSTGRES_PASSWORD"
                "STAGING_REDIS_PASSWORD"
                "STAGING_SECRET_KEY"
            )
            ;;
        production)
            required_vars=(
                "PROD_POSTGRES_PASSWORD"
                "PROD_REDIS_PASSWORD"
                "PROD_SECRET_KEY"
            )
            ;;
        *)
            log_error "未知的部署环境: $DEPLOYMENT_ENV"
            exit 1
            ;;
    esac
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "环境变量 $var 未设置"
            exit 1
        fi
    done
    
    log_success "部署环境检查通过"
}

# 备份当前部署
backup_current_deployment() {
    log_info "备份当前部署..."
    
    local backup_dir="backup-$(date +%Y%m%d_%H%M%S)"
    
    # 创建备份目录
    mkdir -p "$backup_dir"
    
    # 备份配置文件
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$backup_dir/"
    fi
    
    if [ -f ".env" ]; then
        cp .env "$backup_dir/"
    fi
    
    # 备份数据库
    if docker-compose ps | grep -q postgres; then
        log_info "备份数据库..."
        docker-compose exec -T postgres pg_dump -U cet4_user cet4_learning > "$backup_dir/database_backup.sql"
    fi
    
    # 备份Redis数据
    if docker-compose ps | grep -q redis; then
        log_info "备份Redis数据..."
        docker-compose exec -T redis redis-cli --rdb - > "$backup_dir/redis_backup.rdb"
    fi
    
    # 记录当前镜像版本
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" > "$backup_dir/images.txt"
    
    echo "$backup_dir" > .last_backup
    
    log_success "备份完成: $backup_dir"
}

# 拉取最新镜像
pull_latest_images() {
    log_info "拉取最新镜像..."
    
    # 设置镜像标签
    export IMAGE_TAG="$IMAGE_TAG"
    
    # 拉取镜像
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
    else
        docker-compose pull
    fi
    
    log_success "镜像拉取完成"
}

# 更新配置文件
update_configuration() {
    log_info "更新配置文件..."
    
    # 创建环境变量文件
    case $DEPLOYMENT_ENV in
        staging)
            cat > .env << EOF
# Staging Environment Configuration
POSTGRES_PASSWORD=${STAGING_POSTGRES_PASSWORD}
REDIS_PASSWORD=${STAGING_REDIS_PASSWORD}
MINIO_ROOT_USER=${STAGING_MINIO_USER:-minioadmin}
MINIO_ROOT_PASSWORD=${STAGING_MINIO_PASSWORD:-minioadmin123}
SECRET_KEY=${STAGING_SECRET_KEY}
DEEPSEEK_API_KEYS=${DEEPSEEK_API_KEYS}
ALLOWED_HOSTS=staging.cet4-learning.com,localhost
CORS_ORIGINS=https://staging.cet4-learning.com
GRAFANA_PASSWORD=${STAGING_GRAFANA_PASSWORD:-admin123}
ENVIRONMENT=staging
IMAGE_TAG=${IMAGE_TAG}
EOF
            ;;
        production)
            cat > .env << EOF
# Production Environment Configuration
POSTGRES_PASSWORD=${PROD_POSTGRES_PASSWORD}
REDIS_PASSWORD=${PROD_REDIS_PASSWORD}
MINIO_ROOT_USER=${PROD_MINIO_USER:-minioadmin}
MINIO_ROOT_PASSWORD=${PROD_MINIO_PASSWORD:-minioadmin123}
SECRET_KEY=${PROD_SECRET_KEY}
DEEPSEEK_API_KEYS=${DEEPSEEK_API_KEYS}
ALLOWED_HOSTS=cet4-learning.com,www.cet4-learning.com
CORS_ORIGINS=https://cet4-learning.com,https://www.cet4-learning.com
GRAFANA_PASSWORD=${PROD_GRAFANA_PASSWORD:-admin123}
ENVIRONMENT=production
IMAGE_TAG=${IMAGE_TAG}
EOF
            ;;
    esac
    
    log_success "配置文件更新完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 停止现有服务
    docker-compose down --remove-orphans || true
    
    # 启动新服务
    if [ "$DEPLOYMENT_ENV" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local elapsed=0
    local interval=10
    
    while [ $elapsed -lt $timeout ]; do
        # 检查应用健康状态
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "应用服务就绪"
            return 0
        fi
        
        log_info "等待服务启动... (${elapsed}s/${timeout}s)"
        sleep $interval
        elapsed=$((elapsed + interval))
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
    if docker-compose exec -T app python -c "
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
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "✅ Redis连接检查通过"
        checks_passed=$((checks_passed + 1))
    else
        log_error "❌ Redis连接检查失败"
    fi
    
    # 检查Nginx状态
    if curl -f http://localhost/health >/dev/null 2>&1; then
        log_success "✅ Nginx健康检查通过"
        checks_passed=$((checks_passed + 1))
    else
        log_error "❌ Nginx健康检查失败"
    fi
    
    # 检查容器状态
    local unhealthy_containers=$(docker-compose ps --filter "health=unhealthy" -q | wc -l)
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

# 运行部署后测试
run_deployment_tests() {
    log_info "运行部署后测试..."
    
    # 基本API测试
    log_info "测试基本API功能..."
    
    # 测试健康检查端点
    if ! curl -f http://localhost:8000/health; then
        log_error "健康检查端点测试失败"
        return 1
    fi
    
    # 测试API文档端点
    if ! curl -f http://localhost:8000/docs >/dev/null 2>&1; then
        log_error "API文档端点测试失败"
        return 1
    fi
    
    # 测试静态文件服务
    if ! curl -f http://localhost/ >/dev/null 2>&1; then
        log_error "静态文件服务测试失败"
        return 1
    fi
    
    log_success "部署后测试通过"
}

# 回滚部署
rollback_deployment() {
    if [ "$ROLLBACK_ENABLED" != "true" ]; then
        log_warning "回滚功能已禁用"
        return 1
    fi
    
    log_warning "开始回滚部署..."
    
    if [ ! -f ".last_backup" ]; then
        log_error "未找到备份信息，无法回滚"
        return 1
    fi
    
    local backup_dir=$(cat .last_backup)
    
    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        return 1
    fi
    
    # 停止当前服务
    docker-compose down --remove-orphans
    
    # 恢复配置文件
    if [ -f "$backup_dir/docker-compose.yml" ]; then
        cp "$backup_dir/docker-compose.yml" .
    fi
    
    if [ -f "$backup_dir/.env" ]; then
        cp "$backup_dir/.env" .
    fi
    
    # 启动服务
    docker-compose up -d
    
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
    
    # 清理旧备份（保留最近5个）
    ls -t backup-* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
    
    log_success "资源清理完成"
}

# 发送部署通知
send_deployment_notification() {
    local status=$1
    local message=$2
    
    log_info "发送部署通知..."
    
    # 这里可以集成Slack、钉钉、邮件等通知方式
    # 示例：Slack通知
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 部署通知\\n环境: $DEPLOYMENT_ENV\\n状态: $status\\n消息: $message\\n时间: $(date)\"}" \
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
    echo "  --env ENVIRONMENT       部署环境 (staging|production)"
    echo "  --image-tag TAG         镜像标签"
    echo "  --no-backup             跳过备份"
    echo "  --no-rollback           禁用回滚"
    echo "  --health-timeout N      健康检查超时时间（秒）"
    echo ""
    echo "环境变量:"
    echo "  DEPLOYMENT_ENV          部署环境"
    echo "  IMAGE_TAG              镜像标签"
    echo "  HEALTH_CHECK_TIMEOUT    健康检查超时时间"
    echo "  ROLLBACK_ENABLED        是否启用回滚"
}

# 主函数
main() {
    local SKIP_BACKUP=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --env)
                DEPLOYMENT_ENV="$2"
                shift 2
                ;;
            --image-tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --no-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --no-rollback)
                ROLLBACK_ENABLED=false
                shift
                ;;
            --health-timeout)
                HEALTH_CHECK_TIMEOUT="$2"
                shift 2
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "开始部署到 $DEPLOYMENT_ENV 环境..."
    
    # 执行部署流程
    check_deployment_environment
    
    if [ "$SKIP_BACKUP" != "true" ]; then
        backup_current_deployment
    fi
    
    pull_latest_images
    update_configuration
    start_services
    
    if wait_for_services && run_health_checks && run_deployment_tests; then
        cleanup_old_resources
        send_deployment_notification "成功" "部署成功完成"
        log_success "部署成功完成！"
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
