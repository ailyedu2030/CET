#!/bin/bash

# GitHub Secrets配置脚本
# 用于配置CET4学习系统所需的所有GitHub Secrets

echo "🔐 GitHub Secrets配置向导"
echo "=================================="

echo "📋 需要配置的Secrets清单:"
echo ""

echo "🔑 **必需的Secrets (用于CI/CD工作流):**"
echo ""

echo "1. 🤖 **AI服务配置**"
echo "   DEEPSEEK_API_KEYS - DeepSeek AI API密钥"
echo ""

echo "2. 🚀 **测试环境部署**"
echo "   STAGING_HOST - 测试服务器地址"
echo "   STAGING_USER - 测试服务器用户名"
echo "   STAGING_SSH_KEY - 测试服务器SSH私钥"
echo "   STAGING_PORT - 测试服务器SSH端口 (默认22)"
echo "   STAGING_POSTGRES_PASSWORD - 测试环境数据库密码"
echo "   STAGING_REDIS_PASSWORD - 测试环境Redis密码"
echo "   STAGING_MINIO_USER - 测试环境MinIO用户名"
echo "   STAGING_MINIO_PASSWORD - 测试环境MinIO密码"
echo "   STAGING_SECRET_KEY - 测试环境应用密钥"
echo "   STAGING_GRAFANA_PASSWORD - 测试环境Grafana密码"
echo ""

echo "3. 🏭 **生产环境部署**"
echo "   PROD_HOST - 生产服务器地址"
echo "   PROD_USER - 生产服务器用户名"
echo "   PROD_SSH_KEY - 生产服务器SSH私钥"
echo "   PROD_PORT - 生产服务器SSH端口 (默认22)"
echo "   PROD_POSTGRES_PASSWORD - 生产环境数据库密码"
echo "   PROD_REDIS_PASSWORD - 生产环境Redis密码"
echo "   PROD_MINIO_USER - 生产环境MinIO用户名"
echo "   PROD_MINIO_PASSWORD - 生产环境MinIO密码"
echo "   PROD_SECRET_KEY - 生产环境应用密钥"
echo "   PROD_GRAFANA_PASSWORD - 生产环境Grafana密码"
echo ""

echo "4. 📢 **通知配置 (可选)**"
echo "   SLACK_WEBHOOK - Slack通知Webhook URL"
echo ""

echo "=================================="
echo ""

echo "🛠️ **配置方法:**"
echo ""

echo "**方法1: 通过GitHub网页界面配置 (推荐)**"
echo "1. 访问: https://github.com/ailyedu2030/CET/settings/secrets/actions"
echo "2. 点击 'New repository secret'"
echo "3. 输入Secret名称和值"
echo "4. 点击 'Add secret'"
echo ""

echo "**方法2: 使用GitHub CLI配置**"
echo "如果您已安装并认证了GitHub CLI:"
echo ""

# 生成GitHub CLI命令示例
cat << 'EOF'
# 基本配置示例 (请替换为实际值)
gh secret set DEEPSEEK_API_KEYS --body "your-deepseek-api-keys"

# 测试环境配置
gh secret set STAGING_HOST --body "staging.example.com"
gh secret set STAGING_USER --body "deploy"
gh secret set STAGING_SSH_KEY --body "$(cat ~/.ssh/staging_key)"
gh secret set STAGING_PORT --body "22"
gh secret set STAGING_POSTGRES_PASSWORD --body "$(openssl rand -base64 32)"
gh secret set STAGING_REDIS_PASSWORD --body "$(openssl rand -base64 32)"
gh secret set STAGING_MINIO_USER --body "minio"
gh secret set STAGING_MINIO_PASSWORD --body "$(openssl rand -base64 32)"
gh secret set STAGING_SECRET_KEY --body "$(openssl rand -base64 64)"
gh secret set STAGING_GRAFANA_PASSWORD --body "$(openssl rand -base64 32)"

# 生产环境配置
gh secret set PROD_HOST --body "production.example.com"
gh secret set PROD_USER --body "deploy"
gh secret set PROD_SSH_KEY --body "$(cat ~/.ssh/production_key)"
gh secret set PROD_PORT --body "22"
gh secret set PROD_POSTGRES_PASSWORD --body "$(openssl rand -base64 32)"
gh secret set PROD_REDIS_PASSWORD --body "$(openssl rand -base64 32)"
gh secret set PROD_MINIO_USER --body "minio"
gh secret set PROD_MINIO_PASSWORD --body "$(openssl rand -base64 32)"
gh secret set PROD_SECRET_KEY --body "$(openssl rand -base64 64)"
gh secret set PROD_GRAFANA_PASSWORD --body "$(openssl rand -base64 32)"

# 通知配置 (可选)
gh secret set SLACK_WEBHOOK --body "https://hooks.slack.com/services/..."
EOF

echo ""
echo "=================================="
echo ""

echo "⚠️ **重要提示:**"
echo ""
echo "1. **最小配置**: 如果您只想让CI工作流通过，只需配置:"
echo "   - DEEPSEEK_API_KEYS (如果使用AI功能)"
echo ""
echo "2. **跳过部署**: 如果暂时不需要自动部署，可以:"
echo "   - 禁用CD工作流: 重命名 .github/workflows/cd.yml 为 cd.yml.disabled"
echo "   - 或者配置基本的占位符值"
echo ""
echo "3. **安全建议**:"
echo "   - 使用强密码和随机密钥"
echo "   - 定期轮换密钥"
echo "   - 限制SSH密钥权限"
echo ""

echo "🔧 **快速修复工作流失败:**"
echo ""
echo "如果您想快速让所有工作流通过，可以运行:"
echo "./scripts/disable-deployment-workflows.sh"
echo ""

echo "=================================="
echo "📚 更多信息请查看:"
echo "- GitHub Secrets文档: https://docs.github.com/en/actions/security-guides/encrypted-secrets"
echo "- 项目部署文档: docs/deployment.md"
echo "=================================="
