#!/bin/bash

# 英语四级学习系统 - Docker构建脚本
# 用于构建和管理Docker镜像

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="cet4-learning"
IMAGE_TAG=${1:-latest}
BUILD_CONTEXT="."

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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未启动，请启动Docker服务"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 检查Docker Compose是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker Compose环境检查通过"
}

# 清理旧镜像
cleanup_old_images() {
    log_info "清理旧的Docker镜像..."
    
    # 删除悬空镜像
    docker image prune -f
    
    # 删除旧版本镜像（保留最新3个版本）
    OLD_IMAGES=$(docker images "${PROJECT_NAME}" --format "table {{.Repository}}:{{.Tag}}" | tail -n +2 | tail -n +4)
    if [ ! -z "$OLD_IMAGES" ]; then
        echo "$OLD_IMAGES" | xargs docker rmi -f || true
    fi
    
    log_success "镜像清理完成"
}

# 构建主应用镜像
build_app_image() {
    log_info "构建主应用镜像..."
    
    # 检查Dockerfile是否存在
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile不存在"
        exit 1
    fi
    
    # 构建镜像
    docker build \
        --tag "${PROJECT_NAME}:${IMAGE_TAG}" \
        --tag "${PROJECT_NAME}:latest" \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
        --build-arg VERSION=${IMAGE_TAG} \
        ${BUILD_CONTEXT}
    
    log_success "主应用镜像构建完成: ${PROJECT_NAME}:${IMAGE_TAG}"
}

# 验证镜像
validate_image() {
    log_info "验证Docker镜像..."
    
    # 检查镜像是否存在
    if ! docker images "${PROJECT_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}:{{.Tag}}" | grep -q "${PROJECT_NAME}:${IMAGE_TAG}"; then
        log_error "镜像构建失败"
        exit 1
    fi
    
    # 检查镜像大小
    IMAGE_SIZE=$(docker images "${PROJECT_NAME}:${IMAGE_TAG}" --format "table {{.Size}}" | tail -n 1)
    log_info "镜像大小: ${IMAGE_SIZE}"
    
    # 运行基本健康检查
    log_info "运行镜像健康检查..."
    CONTAINER_ID=$(docker run -d --rm "${PROJECT_NAME}:${IMAGE_TAG}")
    sleep 10
    
    if docker ps | grep -q "${CONTAINER_ID}"; then
        log_success "镜像健康检查通过"
        docker stop "${CONTAINER_ID}" > /dev/null
    else
        log_error "镜像健康检查失败"
        docker logs "${CONTAINER_ID}" || true
        exit 1
    fi
}

# 生成镜像信息
generate_image_info() {
    log_info "生成镜像信息..."
    
    cat > image-info.json << EOF
{
    "name": "${PROJECT_NAME}",
    "tag": "${IMAGE_TAG}",
    "build_date": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "git_commit": "$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")",
    "docker_version": "$(docker --version)",
    "image_id": "$(docker images "${PROJECT_NAME}:${IMAGE_TAG}" --format "{{.ID}}")",
    "image_size": "$(docker images "${PROJECT_NAME}:${IMAGE_TAG}" --format "{{.Size}}")"
}
EOF
    
    log_success "镜像信息已保存到 image-info.json"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项] [镜像标签]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -c, --clean    构建前清理旧镜像"
    echo "  -v, --validate 构建后验证镜像"
    echo "  --no-cache     不使用缓存构建"
    echo ""
    echo "示例:"
    echo "  $0                    # 构建latest标签"
    echo "  $0 v1.0.0            # 构建v1.0.0标签"
    echo "  $0 -c v1.0.0         # 清理后构建v1.0.0标签"
    echo "  $0 -v latest         # 构建并验证latest标签"
}

# 主函数
main() {
    local CLEAN_IMAGES=false
    local VALIDATE_IMAGE=false
    local NO_CACHE=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--clean)
                CLEAN_IMAGES=true
                shift
                ;;
            -v|--validate)
                VALIDATE_IMAGE=true
                shift
                ;;
            --no-cache)
                NO_CACHE=true
                shift
                ;;
            -*)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                IMAGE_TAG=$1
                shift
                ;;
        esac
    done
    
    log_info "开始构建Docker镜像: ${PROJECT_NAME}:${IMAGE_TAG}"
    
    # 环境检查
    check_docker
    check_docker_compose
    
    # 清理旧镜像
    if [ "$CLEAN_IMAGES" = true ]; then
        cleanup_old_images
    fi
    
    # 添加no-cache选项
    if [ "$NO_CACHE" = true ]; then
        BUILD_CONTEXT="${BUILD_CONTEXT} --no-cache"
    fi
    
    # 构建镜像
    build_app_image
    
    # 验证镜像
    if [ "$VALIDATE_IMAGE" = true ]; then
        validate_image
    fi
    
    # 生成镜像信息
    generate_image_info
    
    log_success "Docker镜像构建完成!"
    log_info "镜像名称: ${PROJECT_NAME}:${IMAGE_TAG}"
    log_info "使用以下命令启动服务:"
    log_info "  docker-compose up -d"
}

# 执行主函数
main "$@"
