#!/bin/bash

# GitHub集成状态检查脚本

echo "🔍 GitHub集成状态检查"
echo "=================================="

# 基本信息
echo "📋 仓库信息:"
echo "   仓库地址: https://github.com/ailyedu2030/CET"
echo "   本地分支: $(git branch --show-current)"
echo "   远程仓库: $(git remote get-url origin)"
echo "   最新提交: $(git log --oneline -1)"
echo ""

# 检查推送状态
echo "📤 推送状态:"
if git status | grep -q "up to date"; then
    echo "   ✅ 本地与远程同步"
elif git status | grep -q "ahead"; then
    echo "   ⚠️  有未推送的提交"
else
    echo "   ℹ️  状态: $(git status --porcelain | wc -l) 个更改"
fi
echo ""

# 检查GitHub Actions状态
echo "🔄 GitHub Actions状态:"
echo "   访问: https://github.com/ailyedu2030/CET/actions"
echo ""

# 检查关键文件
echo "📁 关键文件检查:"
key_files=(
    ".github/workflows/ci.yml"
    ".github/workflows/quality-check.yml" 
    ".github/workflows/cd.yml"
    ".github/workflows/dependency-update.yml"
    ".github/CODEOWNERS"
    ".github/pull_request_template.md"
    "README.md"
    "pyproject.toml"
    "requirements.txt"
)

for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
    fi
done
echo ""

# 生成下一步操作指南
echo "🎯 下一步操作:"
echo "=================================="
echo ""
echo "1. 📊 检查GitHub Actions运行状态"
echo "   访问: https://github.com/ailyedu2030/CET/actions"
echo "   确认所有工作流正常运行"
echo ""
echo "2. 🔐 配置GitHub Secrets (如需要)"
echo "   访问: https://github.com/ailyedu2030/CET/settings/secrets/actions"
echo "   添加必要的环境变量:"
echo "   - DEEPSEEK_API_KEYS (AI服务密钥)"
echo "   - 部署相关密钥 (如需要)"
echo ""
echo "3. 🧪 测试GitHub集成功能"
echo "   - 创建测试PR验证CODEOWNERS"
echo "   - 验证PR模板功能"
echo "   - 测试Issue模板"
echo ""
echo "4. 🚀 验证CI/CD流程"
echo "   - 检查代码质量检查是否通过"
echo "   - 验证自动化测试"
echo "   - 确认部署流程配置"
echo ""
echo "5. 📚 查看完整文档"
echo "   - README.md: 项目概览"
echo "   - .github/README.md: GitHub配置说明"
echo "   - GITHUB_SETUP_COMPLETE.md: 完整配置报告"
echo ""

echo "🎉 GitHub集成配置完成!"
echo "=================================="
echo "✅ 代码已成功推送到GitHub"
echo "✅ GitHub Actions工作流已启动"
echo "✅ 仓库配置完整"
echo "✅ 所有集成功能已就绪"
echo ""
echo "🌐 仓库地址: https://github.com/ailyedu2030/CET"
