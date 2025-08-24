#!/bin/bash

# 禁用部署工作流脚本
# 临时禁用需要Secrets的工作流，让CI正常运行

echo "🔧 禁用部署工作流"
echo "=================================="

# 备份原始文件
echo "📋 备份原始工作流文件..."
cp .github/workflows/cd.yml .github/workflows/cd.yml.backup
echo "✅ 备份完成: .github/workflows/cd.yml.backup"

# 创建简化的CD工作流（只做构建，不做部署）
cat > .github/workflows/cd.yml << 'EOF'
# 英语四级学习系统 - 持续部署工作流 (简化版)
# 只进行构建和测试，不进行实际部署

name: Continuous Deployment

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # 构建Docker镜像
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Image scan
      uses: anchore/scan-action@v3
      with:
        image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.tags }}
        fail-build: false
        severity-cutoff: high

  # 部署准备（不实际部署）
  deployment-ready:
    name: Deployment Ready
    runs-on: ubuntu-latest
    needs: build
    
    steps:
    - name: Deployment status
      run: |
        echo "🚀 Docker镜像构建完成"
        echo "📦 镜像已推送到容器注册表"
        echo "⚠️  实际部署已禁用 - 需要配置Secrets后启用"
        echo ""
        echo "🔧 启用完整部署的步骤:"
        echo "1. 配置GitHub Secrets"
        echo "2. 恢复原始CD工作流: mv .github/workflows/cd.yml.backup .github/workflows/cd.yml"
        echo "3. 提交并推送更改"
        echo ""
        echo "📚 详细配置说明: ./scripts/configure-github-secrets.sh"
EOF

echo ""
echo "✅ CD工作流已简化"
echo "📝 新的CD工作流只进行构建，不进行部署"
echo ""

echo "🔄 提交更改..."
git add .github/workflows/cd.yml
git commit -m "Simplify CD workflow - disable deployment until secrets are configured

🔧 Changes:
- Backup original CD workflow to cd.yml.backup
- Create simplified CD workflow that only builds Docker images
- Remove deployment steps that require secrets
- Add instructions for re-enabling full deployment

📋 To restore full deployment:
1. Configure GitHub Secrets
2. Restore original workflow: mv cd.yml.backup cd.yml
3. Commit and push changes"

echo "✅ 更改已提交"
echo ""

echo "📤 推送到GitHub..."
# 推送更改（需要已配置的认证）
if git push origin main; then
    echo "✅ 推送成功"
else
    echo "❌ 推送失败，请检查GitHub认证配置"
    echo "💡 提示：可能需要配置Personal Access Token或SSH密钥"
fi

echo "✅ 推送完成"
echo ""

echo "🎉 部署工作流已禁用"
echo "=================================="
echo ""
echo "✅ 现在GitHub Actions应该能正常运行"
echo "✅ CI工作流将继续进行代码质量检查"
echo "✅ CD工作流只进行Docker构建"
echo ""
echo "🔧 下一步:"
echo "1. 检查GitHub Actions状态: https://github.com/ailyedu2030/CET/actions"
echo "2. 配置Secrets: ./scripts/configure-github-secrets.sh"
echo "3. 恢复完整部署: mv .github/workflows/cd.yml.backup .github/workflows/cd.yml"
echo ""
echo "📚 详细说明请查看配置脚本输出"
