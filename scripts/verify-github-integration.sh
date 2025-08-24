#!/bin/bash

# GitHub集成验证脚本

set -e

echo "🔍 GitHub集成验证脚本"
echo "=================================="

REPO_URL="https://github.com/ailyedu2030/CET"
API_URL="https://api.github.com/repos/ailyedu2030/CET"

# 1. 验证仓库存在
echo "1. 验证GitHub仓库..."
if curl -s "$API_URL" | grep -q '"name": "CET"'; then
    echo "✅ 仓库存在: $REPO_URL"
    
    # 获取仓库信息
    repo_info=$(curl -s "$API_URL")
    echo "   创建时间: $(echo "$repo_info" | grep '"created_at"' | cut -d'"' -f4)"
    echo "   默认分支: $(echo "$repo_info" | grep '"default_branch"' | cut -d'"' -f4)"
    echo "   是否私有: $(echo "$repo_info" | grep '"private"' | cut -d':' -f2 | cut -d',' -f1)"
else
    echo "❌ 仓库不存在或无法访问"
    echo "请先在GitHub上创建仓库: https://github.com/new"
    exit 1
fi

# 2. 验证本地Git配置
echo ""
echo "2. 验证本地Git配置..."
echo "   远程仓库: $(git remote get-url origin)"
echo "   当前分支: $(git branch --show-current)"
echo "   提交数量: $(git rev-list --count HEAD 2>/dev/null || echo '0')"

# 检查是否有未推送的提交
if git status | grep -q "Your branch is ahead"; then
    echo "⚠️  有未推送的提交"
    echo "   未推送提交数: $(git rev-list --count origin/main..HEAD 2>/dev/null || echo 'unknown')"
elif git status | grep -q "up to date"; then
    echo "✅ 本地分支与远程同步"
else
    echo "⚠️  分支状态未知，可能需要首次推送"
fi

# 3. 验证GitHub Actions工作流文件
echo ""
echo "3. 验证GitHub Actions工作流..."
workflows_dir=".github/workflows"
if [ -d "$workflows_dir" ]; then
    echo "✅ 工作流目录存在: $workflows_dir"
    
    # 检查各个工作流文件
    workflows=("ci.yml" "quality-check.yml" "cd.yml" "dependency-update.yml")
    for workflow in "${workflows[@]}"; do
        if [ -f "$workflows_dir/$workflow" ]; then
            echo "   ✅ $workflow"
        else
            echo "   ❌ $workflow (缺失)"
        fi
    done
else
    echo "❌ 工作流目录不存在"
fi

# 4. 验证GitHub集成文件
echo ""
echo "4. 验证GitHub集成文件..."
github_files=(
    ".github/CODEOWNERS"
    ".github/pull_request_template.md"
    ".github/ISSUE_TEMPLATE/code-quality.md"
    ".github/README.md"
)

for file in "${github_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
    fi
done

# 5. 验证项目配置文件
echo ""
echo "5. 验证项目配置文件..."
config_files=(
    "pyproject.toml"
    "requirements.txt"
    ".pre-commit-config.yaml"
    ".gitignore"
    ".gitattributes"
    ".editorconfig"
    "docker-compose.yml"
    "Dockerfile"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
    fi
done

# 6. 验证代码质量工具
echo ""
echo "6. 验证代码质量工具..."
if [ -f "scripts/quality-check-local.sh" ]; then
    echo "✅ 本地质量检查脚本存在"
    
    # 运行快速质量检查
    echo "   运行快速质量检查..."
    if ./scripts/quality-check-local.sh > /dev/null 2>&1; then
        echo "   ✅ 质量检查通过"
    else
        echo "   ⚠️  质量检查有警告，查看详细报告"
    fi
else
    echo "❌ 质量检查脚本缺失"
fi

# 7. 生成推送后检查清单
echo ""
echo "7. 推送后检查清单..."
echo "=================================="
echo ""
echo "📋 推送代码后请检查以下项目:"
echo ""
echo "🌐 **GitHub仓库页面检查**"
echo "   1. 访问: $REPO_URL"
echo "   2. ✅ 确认所有文件已上传"
echo "   3. ✅ 确认README.md显示正常"
echo "   4. ✅ 确认目录结构完整"
echo ""
echo "⚙️  **GitHub Actions检查**"
echo "   1. 访问: $REPO_URL/actions"
echo "   2. ✅ 确认CI工作流运行"
echo "   3. ✅ 确认所有检查通过"
echo "   4. ✅ 查看任何失败的步骤"
echo ""
echo "🔐 **GitHub Secrets配置**"
echo "   1. 访问: $REPO_URL/settings/secrets/actions"
echo "   2. ✅ 添加DEEPSEEK_API_KEYS"
echo "   3. ✅ 添加部署相关Secrets"
echo "   4. ✅ 添加通知Secrets (可选)"
echo ""
echo "🧪 **功能测试**"
echo "   1. ✅ 创建测试PR验证CODEOWNERS"
echo "   2. ✅ 创建测试Issue验证模板"
echo "   3. ✅ 验证分支保护规则"
echo "   4. ✅ 测试CI/CD流程"
echo ""

# 8. 生成推送命令
echo "🚀 **推送命令参考**"
echo "=================================="
echo ""
echo "如果还未推送，使用以下命令:"
echo ""
echo "# 方法1: 使用Personal Access Token"
echo "git remote set-url origin https://YOUR_TOKEN@github.com/ailyedu2030/CET.git"
echo "git push -u origin main"
echo "git remote set-url origin https://github.com/ailyedu2030/CET.git"
echo ""
echo "# 方法2: 使用GitHub CLI (如果已认证)"
echo "gh repo create CET --public --source=. --remote=origin --push"
echo ""
echo "# 方法3: 使用SSH (如果已配置SSH密钥)"
echo "git remote set-url origin git@github.com:ailyedu2030/CET.git"
echo "git push -u origin main"
echo ""

echo "=================================="
echo "✅ GitHub集成验证完成"
echo ""
echo "📖 详细配置指南: GITHUB_SETUP_MANUAL.md"
echo "📊 完整配置报告: GITHUB_SETUP_COMPLETE.md"
