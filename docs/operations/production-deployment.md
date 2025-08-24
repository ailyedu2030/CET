# 英语四级学习系统 - 生产环境部署指南

## 概述

本文档详细说明了英语四级学习系统在生产环境的部署、配置和运维流程。

## 系统架构

### 服务组件
- **应用服务**: FastAPI应用 (Python 3.11)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **向量数据库**: Milvus 2.3
- **对象存储**: MinIO
- **反向代理**: Nginx
- **任务队列**: Celery + Redis
- **监控**: Prometheus + Grafana

### 网络架构
```
Internet → Nginx (80/443) → FastAPI App (8000) → PostgreSQL (5432)
                                              → Redis (6379)
                                              → Milvus (19530)
                                              → MinIO (9000)
```

## 部署前准备

### 1. 服务器要求

**最低配置**:
- CPU: 4核心
- 内存: 8GB
- 存储: 100GB SSD
- 网络: 100Mbps

**推荐配置**:
- CPU: 8核心
- 内存: 16GB
- 存储: 200GB SSD
- 网络: 1Gbps

### 2. 系统要求

- 操作系统: Ubuntu 20.04+ / CentOS 8+
- Docker: 20.10+
- Docker Compose: 2.0+
- 域名: 已解析到服务器IP

### 3. 端口配置

**对外开放端口**:
- 80 (HTTP)
- 443 (HTTPS)
- 22 (SSH)

**内部端口**:
- 5432 (PostgreSQL)
- 6379 (Redis)
- 8000 (应用服务)
- 9000 (MinIO)
- 19530 (Milvus)

## 部署流程

### 1. 环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建项目目录
sudo mkdir -p /opt/cet4-learning
sudo chown $USER:$USER /opt/cet4-learning
```

### 2. 代码部署

```bash
# 克隆代码
cd /opt/cet4-learning
git clone https://github.com/your-org/cet4-learning-system.git .

# 切换到生产分支
git checkout main
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp deployment/production/env.prod deployment/production/.env

# 编辑环境变量
nano deployment/production/.env
```

**重要配置项**:
```bash
# 安全密钥 (必须修改)
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# 数据库密码 (必须修改)
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-secure-redis-password

# 域名配置
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# AI服务配置
DEEPSEEK_API_KEYS=your-api-key-1,your-api-key-2

# 邮件配置
SMTP_HOST=your-smtp-host
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
```

### 4. SSL证书配置

```bash
# 配置SSL证书
sudo ./deployment/scripts/setup-ssl.sh --domain your-domain.com --email admin@your-domain.com
```

### 5. 执行部署

```bash
# 执行生产环境部署
sudo ./deployment/scripts/deploy-production.sh --image-tag latest
```

## 监控配置

### 1. Prometheus监控

监控配置文件: `deployment/monitoring/prometheus.yml`

**监控指标**:
- 系统资源 (CPU、内存、磁盘)
- 应用性能 (响应时间、错误率)
- 数据库状态 (连接数、查询性能)
- 服务可用性 (健康检查)

### 2. 告警规则

告警配置文件: `deployment/monitoring/alert_rules.yml`

**告警类型**:
- 系统资源告警 (CPU > 80%, 内存 > 80%)
- 应用服务告警 (服务不可用、响应时间过长)
- 数据库告警 (连接数过多、查询缓慢)
- SSL证书告警 (即将过期)

### 3. 日志管理

**日志位置**:
- 应用日志: `/opt/cet4-learning/logs/`
- Nginx日志: `/var/log/nginx/`
- 系统日志: `/var/log/`

**日志轮转**:
```bash
# 配置logrotate
sudo nano /etc/logrotate.d/cet4-learning
```

## 运维操作

### 1. 服务管理

```bash
# 查看服务状态
docker-compose -f deployment/production/docker-compose.prod.yml ps

# 启动服务
docker-compose -f deployment/production/docker-compose.prod.yml up -d

# 停止服务
docker-compose -f deployment/production/docker-compose.prod.yml down

# 重启特定服务
docker-compose -f deployment/production/docker-compose.prod.yml restart app

# 查看日志
docker-compose -f deployment/production/docker-compose.prod.yml logs -f app
```

### 2. 数据库管理

```bash
# 连接数据库
docker-compose -f deployment/production/docker-compose.prod.yml exec postgres psql -U cet4_user_prod -d cet4_learning_prod

# 数据库备份
docker-compose -f deployment/production/docker-compose.prod.yml exec postgres pg_dump -U cet4_user_prod cet4_learning_prod > backup_$(date +%Y%m%d).sql

# 数据库恢复
docker-compose -f deployment/production/docker-compose.prod.yml exec -T postgres psql -U cet4_user_prod -d cet4_learning_prod < backup.sql
```

### 3. 缓存管理

```bash
# 连接Redis
docker-compose -f deployment/production/docker-compose.prod.yml exec redis redis-cli

# 清空缓存
docker-compose -f deployment/production/docker-compose.prod.yml exec redis redis-cli FLUSHALL

# 查看缓存统计
docker-compose -f deployment/production/docker-compose.prod.yml exec redis redis-cli INFO
```

### 4. 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新部署
sudo ./deployment/scripts/deploy-production.sh --image-tag latest
```

### 5. 回滚操作

```bash
# 回滚到上一个版本
sudo ./deployment/scripts/deploy-production.sh --rollback
```

## 性能优化

### 1. 数据库优化

```sql
-- 查看慢查询
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- 分析表统计信息
ANALYZE;

-- 重建索引
REINDEX DATABASE cet4_learning_prod;
```

### 2. 缓存优化

```bash
# 查看缓存命中率
redis-cli INFO stats | grep keyspace

# 优化缓存配置
# 编辑 redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### 3. Nginx优化

```nginx
# 编辑 nginx.conf
worker_processes auto;
worker_connections 2048;

# 启用gzip压缩
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;

# 配置缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 安全配置

### 1. 防火墙配置

```bash
# 配置UFW防火墙
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
```

### 2. SSL安全

```bash
# 检查SSL配置
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# 测试SSL评级
curl -s "https://api.ssllabs.com/api/v3/analyze?host=your-domain.com"
```

### 3. 访问控制

```nginx
# 限制管理后台访问
location /admin/ {
    allow 192.168.1.0/24;  # 允许内网访问
    deny all;              # 拒绝其他访问
}

# 限制API访问频率
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ {
    limit_req zone=api burst=20 nodelay;
}
```

## 故障排除

### 1. 常见问题

**服务无法启动**:
```bash
# 检查端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

**数据库连接失败**:
```bash
# 检查数据库状态
docker-compose -f deployment/production/docker-compose.prod.yml exec postgres pg_isready

# 检查连接数
docker-compose -f deployment/production/docker-compose.prod.yml exec postgres psql -U cet4_user_prod -c "SELECT count(*) FROM pg_stat_activity;"
```

**SSL证书问题**:
```bash
# 检查证书有效期
openssl x509 -in /opt/cet4-learning/deployment/production/ssl/fullchain.pem -noout -dates

# 手动更新证书
sudo certbot renew --force-renewal
```

### 2. 日志分析

```bash
# 查看错误日志
tail -f /var/log/nginx/error.log
docker-compose -f deployment/production/docker-compose.prod.yml logs -f app | grep ERROR

# 分析访问日志
tail -f /var/log/nginx/access.log | grep "5[0-9][0-9]"
```

## 备份策略

### 1. 数据库备份

```bash
# 每日自动备份
0 2 * * * /opt/cet4-learning/scripts/backup-database.sh

# 备份脚本
#!/bin/bash
BACKUP_DIR="/opt/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f /opt/cet4-learning/deployment/production/docker-compose.prod.yml exec postgres pg_dump -U cet4_user_prod cet4_learning_prod > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
```

### 2. 文件备份

```bash
# 备份上传文件
rsync -av /opt/cet4-learning/uploads/ /opt/backups/uploads/

# 备份配置文件
tar -czf /opt/backups/config_$(date +%Y%m%d).tar.gz /opt/cet4-learning/deployment/
```

## 联系信息

- **技术支持**: tech-support@cet4-learning.com
- **运维团队**: ops@cet4-learning.com
- **紧急联系**: +86-xxx-xxxx-xxxx
