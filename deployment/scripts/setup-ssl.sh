#!/bin/bash

# 英语四级学习系统 - SSL证书配置脚本
# 使用Let's Encrypt自动配置SSL证书

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
SSL_DIR="$PROJECT_ROOT/deployment/production/ssl"
CERTBOT_DIR="/etc/letsencrypt"

# 默认配置
DOMAIN=${DOMAIN:-cet4-learning.com}
EMAIL=${EMAIL:-admin@cet4-learning.com}
STAGING=${STAGING:-false}
FORCE_RENEWAL=${FORCE_RENEWAL:-false}

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
    log_info "检查SSL配置依赖..."
    
    # 检查是否为root用户
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限运行此脚本"
        exit 1
    fi
    
    # 检查certbot
    if ! command -v certbot &> /dev/null; then
        log_info "安装certbot..."
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y certbot
        elif command -v yum &> /dev/null; then
            yum install -y certbot
        else
            log_error "无法安装certbot，请手动安装"
            exit 1
        fi
    fi
    
    # 检查openssl
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 验证域名解析
verify_domain_resolution() {
    log_info "验证域名解析..."
    
    local domains=("$DOMAIN" "www.$DOMAIN")
    
    for domain in "${domains[@]}"; do
        log_info "检查域名: $domain"
        
        # 检查A记录
        if ! nslookup "$domain" >/dev/null 2>&1; then
            log_error "域名 $domain 无法解析"
            exit 1
        fi
        
        # 检查HTTP连通性
        if ! curl -s --connect-timeout 10 "http://$domain" >/dev/null 2>&1; then
            log_warning "域名 $domain HTTP连接失败，请确保Nginx正在运行"
        fi
    done
    
    log_success "域名解析验证通过"
}

# 创建SSL目录
create_ssl_directory() {
    log_info "创建SSL目录..."
    
    mkdir -p "$SSL_DIR"
    chmod 755 "$SSL_DIR"
    
    log_success "SSL目录创建完成: $SSL_DIR"
}

# 生成自签名证书（用于测试）
generate_self_signed_certificate() {
    log_info "生成自签名证书（仅用于测试）..."
    
    local cert_file="$SSL_DIR/fullchain.pem"
    local key_file="$SSL_DIR/privkey.pem"
    
    # 生成私钥
    openssl genrsa -out "$key_file" 2048
    
    # 生成证书
    openssl req -new -x509 -key "$key_file" -out "$cert_file" -days 365 \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=CET4 Learning/CN=$DOMAIN"
    
    # 设置权限
    chmod 600 "$key_file"
    chmod 644 "$cert_file"
    
    log_success "自签名证书生成完成"
    log_warning "自签名证书仅用于测试，生产环境请使用Let's Encrypt证书"
}

# 获取Let's Encrypt证书
obtain_letsencrypt_certificate() {
    log_info "获取Let's Encrypt证书..."
    
    local staging_flag=""
    if [ "$STAGING" = "true" ]; then
        staging_flag="--staging"
        log_info "使用Let's Encrypt测试环境"
    fi
    
    local force_flag=""
    if [ "$FORCE_RENEWAL" = "true" ]; then
        force_flag="--force-renewal"
        log_info "强制更新证书"
    fi
    
    # 停止可能占用80端口的服务
    log_info "临时停止Nginx服务..."
    systemctl stop nginx 2>/dev/null || docker-compose -f "$PROJECT_ROOT/deployment/production/docker-compose.prod.yml" stop nginx 2>/dev/null || true
    
    # 获取证书
    certbot certonly \
        --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN,www.$DOMAIN" \
        $staging_flag \
        $force_flag \
        --non-interactive
    
    # 重启Nginx服务
    log_info "重启Nginx服务..."
    systemctl start nginx 2>/dev/null || docker-compose -f "$PROJECT_ROOT/deployment/production/docker-compose.prod.yml" start nginx 2>/dev/null || true
    
    log_success "Let's Encrypt证书获取完成"
}

# 复制证书到项目目录
copy_certificates() {
    log_info "复制证书到项目目录..."
    
    local cert_source="/etc/letsencrypt/live/$DOMAIN"
    
    if [ ! -d "$cert_source" ]; then
        log_error "证书目录不存在: $cert_source"
        exit 1
    fi
    
    # 复制证书文件
    cp "$cert_source/fullchain.pem" "$SSL_DIR/"
    cp "$cert_source/privkey.pem" "$SSL_DIR/"
    
    # 设置权限
    chmod 644 "$SSL_DIR/fullchain.pem"
    chmod 600 "$SSL_DIR/privkey.pem"
    
    # 创建符号链接（可选）
    ln -sf "$cert_source/fullchain.pem" "$SSL_DIR/cert.pem"
    ln -sf "$cert_source/privkey.pem" "$SSL_DIR/key.pem"
    
    log_success "证书复制完成"
}

# 验证证书
verify_certificate() {
    log_info "验证SSL证书..."
    
    local cert_file="$SSL_DIR/fullchain.pem"
    local key_file="$SSL_DIR/privkey.pem"
    
    if [ ! -f "$cert_file" ] || [ ! -f "$key_file" ]; then
        log_error "证书文件不存在"
        exit 1
    fi
    
    # 检查证书有效性
    if ! openssl x509 -in "$cert_file" -noout -checkend 86400; then
        log_error "证书将在24小时内过期"
        exit 1
    fi
    
    # 检查证书和私钥匹配
    cert_hash=$(openssl x509 -noout -modulus -in "$cert_file" | openssl md5)
    key_hash=$(openssl rsa -noout -modulus -in "$key_file" | openssl md5)
    
    if [ "$cert_hash" != "$key_hash" ]; then
        log_error "证书和私钥不匹配"
        exit 1
    fi
    
    # 显示证书信息
    log_info "证书信息:"
    openssl x509 -in "$cert_file" -noout -subject -dates
    
    log_success "证书验证通过"
}

# 配置证书自动更新
setup_auto_renewal() {
    log_info "配置证书自动更新..."
    
    # 创建更新脚本
    cat > /usr/local/bin/renew-cet4-ssl.sh << 'EOF'
#!/bin/bash

# CET4学习系统SSL证书自动更新脚本

LOG_FILE="/var/log/ssl-renewal.log"
PROJECT_ROOT="/opt/cet4-learning"
SSL_DIR="$PROJECT_ROOT/deployment/production/ssl"

log_message() {
    echo "$(date): $1" >> "$LOG_FILE"
}

log_message "开始SSL证书更新检查"

# 更新证书
if certbot renew --quiet --no-self-upgrade; then
    log_message "证书更新成功"
    
    # 复制新证书
    if [ -d "/etc/letsencrypt/live/cet4-learning.com" ]; then
        cp "/etc/letsencrypt/live/cet4-learning.com/fullchain.pem" "$SSL_DIR/"
        cp "/etc/letsencrypt/live/cet4-learning.com/privkey.pem" "$SSL_DIR/"
        chmod 644 "$SSL_DIR/fullchain.pem"
        chmod 600 "$SSL_DIR/privkey.pem"
        log_message "证书文件已更新"
    fi
    
    # 重启Nginx
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
        log_message "Nginx已重新加载"
    elif docker-compose -f "$PROJECT_ROOT/deployment/production/docker-compose.prod.yml" ps nginx | grep -q "Up"; then
        docker-compose -f "$PROJECT_ROOT/deployment/production/docker-compose.prod.yml" exec nginx nginx -s reload
        log_message "Docker Nginx已重新加载"
    fi
    
    log_message "SSL证书更新完成"
else
    log_message "SSL证书更新失败"
    exit 1
fi
EOF
    
    chmod +x /usr/local/bin/renew-cet4-ssl.sh
    
    # 添加到crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/renew-cet4-ssl.sh") | crontab -
    
    log_success "证书自动更新配置完成"
    log_info "证书将在每天凌晨2点自动检查更新"
}

# 测试SSL配置
test_ssl_configuration() {
    log_info "测试SSL配置..."
    
    # 等待Nginx启动
    sleep 5
    
    # 测试HTTPS连接
    if curl -s --connect-timeout 10 "https://$DOMAIN" >/dev/null 2>&1; then
        log_success "HTTPS连接测试通过"
    else
        log_warning "HTTPS连接测试失败，请检查Nginx配置"
    fi
    
    # 测试SSL证书
    if echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -dates; then
        log_success "SSL证书测试通过"
    else
        log_warning "SSL证书测试失败"
    fi
    
    log_info "SSL配置测试完成"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示帮助信息"
    echo "  --domain DOMAIN         指定域名 (默认: cet4-learning.com)"
    echo "  --email EMAIL           指定邮箱 (默认: admin@cet4-learning.com)"
    echo "  --staging               使用Let's Encrypt测试环境"
    echo "  --force-renewal         强制更新证书"
    echo "  --self-signed           生成自签名证书（仅用于测试）"
    echo "  --test-only             仅测试SSL配置"
    echo ""
    echo "环境变量:"
    echo "  DOMAIN                  域名"
    echo "  EMAIL                   邮箱"
    echo "  STAGING                 是否使用测试环境"
    echo "  FORCE_RENEWAL           是否强制更新"
}

# 主函数
main() {
    local SELF_SIGNED=false
    local TEST_ONLY=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --staging)
                STAGING=true
                shift
                ;;
            --force-renewal)
                FORCE_RENEWAL=true
                shift
                ;;
            --self-signed)
                SELF_SIGNED=true
                shift
                ;;
            --test-only)
                TEST_ONLY=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "开始SSL证书配置..."
    log_info "域名: $DOMAIN"
    log_info "邮箱: $EMAIL"
    
    # 仅测试模式
    if [ "$TEST_ONLY" = "true" ]; then
        test_ssl_configuration
        exit 0
    fi
    
    # 执行SSL配置流程
    check_dependencies
    create_ssl_directory
    
    if [ "$SELF_SIGNED" = "true" ]; then
        generate_self_signed_certificate
    else
        verify_domain_resolution
        obtain_letsencrypt_certificate
        copy_certificates
        setup_auto_renewal
    fi
    
    verify_certificate
    test_ssl_configuration
    
    log_success "SSL证书配置完成！"
    log_info "证书位置: $SSL_DIR"
    log_info "证书有效期: $(openssl x509 -in "$SSL_DIR/fullchain.pem" -noout -enddate | cut -d= -f2)"
}

# 执行主函数
main "$@"
