#!/bin/bash

# GitHub访问测试脚本

echo "🔍 GitHub访问测试"
echo "=================================="

# 测试网络连接
echo "1. 测试GitHub网络连接..."
if curl -s --connect-timeout 10 https://github.com > /dev/null; then
    echo "✅ GitHub网络连接正常"
else
    echo "❌ GitHub网络连接失败"
fi

# 测试API访问
echo ""
echo "2. 测试GitHub API访问..."
if curl -s --connect-timeout 10 https://api.github.com/repos/ailyedu2030/CET > /dev/null; then
    echo "✅ GitHub API访问正常"
    
    # 获取仓库信息
    repo_info=$(curl -s https://api.github.com/repos/ailyedu2030/CET)
    if echo "$repo_info" | grep -q '"name": "CET"'; then
        echo "✅ 仓库 ailyedu2030/CET 存在"
        echo "   仓库名称: $(echo "$repo_info" | grep '"name"' | head -1 | cut -d'"' -f4)"
        echo "   创建时间: $(echo "$repo_info" | grep '"created_at"' | cut -d'"' -f4)"
        echo "   默认分支: $(echo "$repo_info" | grep '"default_branch"' | cut -d'"' -f4)"
    else
        echo "❌ 仓库不存在或无法访问"
        echo "API响应: $repo_info"
    fi
else
    echo "❌ GitHub API访问失败"
fi

# 测试Git配置
echo ""
echo "3. 检查Git配置..."
echo "   用户名: $(git config user.name)"
echo "   邮箱: $(git config user.email)"
echo "   远程仓库: $(git remote get-url origin)"

# 测试代理设置
echo ""
echo "4. 检查代理设置..."
if git config --get http.proxy > /dev/null; then
    echo "   HTTP代理: $(git config --get http.proxy)"
else
    echo "   HTTP代理: 未设置"
fi

if git config --get https.proxy > /dev/null; then
    echo "   HTTPS代理: $(git config --get https.proxy)"
else
    echo "   HTTPS代理: 未设置"
fi

# 测试SSH连接
echo ""
echo "5. 测试SSH连接..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH连接成功"
elif ssh -T git@github.com 2>&1 | grep -q "Permission denied"; then
    echo "❌ SSH连接失败 - 权限被拒绝"
    echo "   需要添加SSH密钥到GitHub"
else
    echo "⚠️  SSH连接测试无法完成"
fi

echo ""
echo "=================================="
echo "测试完成"
