#!/bin/bash

# GitHub仓库创建脚本

set -e

echo "🏗️  GitHub仓库创建脚本"
echo "=================================="

REPO_NAME="CET"
REPO_DESCRIPTION="CET4 Learning System - AI-powered English learning platform with comprehensive training modules, adaptive learning algorithms, and intelligent teaching assistance."

echo "📋 仓库信息:"
echo "   名称: $REPO_NAME"
echo "   描述: $REPO_DESCRIPTION"
echo "   用户: ailyedu2030"
echo ""

# 方法1: 使用GitHub CLI
echo "🔧 方法1: 尝试使用GitHub CLI创建仓库..."
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI已安装"
    
    # 检查认证状态
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI已认证"
        
        # 创建仓库
        echo "📝 创建仓库..."
        if gh repo create "$REPO_NAME" --description "$REPO_DESCRIPTION" --public; then
            echo "✅ 仓库创建成功 (GitHub CLI)"
            echo "🌐 仓库地址: https://github.com/ailyedu2030/$REPO_NAME"
            exit 0
        else
            echo "❌ GitHub CLI创建仓库失败"
        fi
    else
        echo "⚠️  GitHub CLI未认证，尝试认证..."
        if gh auth login --web --git-protocol https; then
            echo "✅ GitHub CLI认证成功"
            
            # 创建仓库
            if gh repo create "$REPO_NAME" --description "$REPO_DESCRIPTION" --public; then
                echo "✅ 仓库创建成功 (GitHub CLI)"
                echo "🌐 仓库地址: https://github.com/ailyedu2030/$REPO_NAME"
                exit 0
            else
                echo "❌ GitHub CLI创建仓库失败"
            fi
        else
            echo "❌ GitHub CLI认证失败"
        fi
    fi
else
    echo "❌ GitHub CLI未安装"
fi

# 方法2: 使用Personal Access Token和API
echo ""
echo "🔧 方法2: 使用GitHub API创建仓库..."
echo "需要Personal Access Token来创建仓库"
echo ""
echo "📝 获取Personal Access Token:"
echo "1. 访问: https://github.com/settings/tokens"
echo "2. 点击 'Generate new token (classic)'"
echo "3. 设置名称: CET4-Repo-Creation-$(date +%Y%m%d)"
echo "4. 选择权限: ✅ repo (完整仓库访问)"
echo "5. 点击 'Generate token' 并复制"
echo ""

read -p "请输入您的Personal Access Token: " -s github_token
echo ""

if [ -z "$github_token" ]; then
    echo "❌ Token不能为空"
    exit 1
fi

# 验证token
echo "🔍 验证Token..."
user_info=$(curl -s -H "Authorization: token $github_token" https://api.github.com/user)
if echo "$user_info" | grep -q '"login"'; then
    username=$(echo "$user_info" | grep '"login"' | cut -d'"' -f4)
    echo "✅ Token验证成功，用户: $username"
    
    # 创建仓库
    echo "📝 创建仓库..."
    repo_data='{
        "name": "'$REPO_NAME'",
        "description": "'$REPO_DESCRIPTION'",
        "private": false,
        "has_issues": true,
        "has_projects": true,
        "has_wiki": true,
        "auto_init": false
    }'
    
    response=$(curl -s -w "%{http_code}" -H "Authorization: token $github_token" \
        -H "Content-Type: application/json" \
        -d "$repo_data" \
        https://api.github.com/user/repos)
    
    http_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$http_code" = "201" ]; then
        echo "✅ 仓库创建成功 (GitHub API)"
        repo_url=$(echo "$response_body" | grep '"html_url"' | head -1 | cut -d'"' -f4)
        echo "🌐 仓库地址: $repo_url"
        
        # 配置Git远程仓库
        echo "🔧 配置Git远程仓库..."
        git remote set-url origin "https://github.com/$username/$REPO_NAME.git"
        echo "✅ Git远程仓库已配置"
        
        # 推送代码
        echo "📤 推送代码到GitHub..."
        git remote set-url origin "https://$github_token@github.com/$username/$REPO_NAME.git"
        
        if git push -u origin main; then
            echo "✅ 代码推送成功!"
            
            # 清理URL中的token
            git remote set-url origin "https://github.com/$username/$REPO_NAME.git"
            echo "✅ 远程仓库URL已清理"
        else
            echo "❌ 代码推送失败"
            git remote set-url origin "https://github.com/$username/$REPO_NAME.git"
            exit 1
        fi
        
    elif [ "$http_code" = "422" ]; then
        echo "⚠️  仓库可能已存在"
        echo "API响应: $response_body"
        
        # 尝试直接推送
        echo "🔧 尝试推送到现有仓库..."
        git remote set-url origin "https://$github_token@github.com/$username/$REPO_NAME.git"
        
        if git push -u origin main; then
            echo "✅ 代码推送成功!"
            git remote set-url origin "https://github.com/$username/$REPO_NAME.git"
        else
            echo "❌ 代码推送失败"
            git remote set-url origin "https://github.com/$username/$REPO_NAME.git"
            exit 1
        fi
    else
        echo "❌ 仓库创建失败 (HTTP $http_code)"
        echo "API响应: $response_body"
        exit 1
    fi
else
    echo "❌ Token验证失败"
    echo "响应: $user_info"
    exit 1
fi

echo ""
echo "🎉 GitHub仓库配置完成!"
echo "=================================="
echo "✅ 仓库已创建并推送代码"
echo "🌐 仓库地址: https://github.com/ailyedu2030/$REPO_NAME"
echo ""
echo "🔗 下一步:"
echo "1. 访问仓库检查代码"
echo "2. 配置GitHub Secrets"
echo "3. 验证GitHub Actions"
