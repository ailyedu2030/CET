#!/bin/bash

# GitHub推送脚本 - 使用Personal Access Token
# 用于安全推送代码到GitHub

set -e

echo "🚀 GitHub代码推送脚本"
echo "=================================="

# 检查当前状态
echo "📋 当前项目状态:"
echo "项目目录: $(pwd)"
echo "Git状态: $(git status --porcelain | wc -l) 个未提交更改"
echo "当前分支: $(git branch --show-current)"
echo "提交数量: $(git rev-list --count HEAD)"
echo "远程仓库: $(git remote get-url origin)"
echo ""

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  发现未提交的更改:"
    git status --short
    echo ""
    read -p "是否先提交这些更改? (y/n): " commit_changes
    if [ "$commit_changes" = "y" ]; then
        git add .
        read -p "请输入提交信息: " commit_msg
        git commit -m "$commit_msg"
        echo "✅ 更改已提交"
    fi
fi

echo "🔐 GitHub认证配置"
echo "--------------------------------"
echo "请选择认证方式:"
echo "1. 使用Personal Access Token（推荐）"
echo "2. 使用现有的Git凭据"
echo "3. 配置SSH密钥"
echo ""

read -p "请选择 (1-3): " auth_method

case $auth_method in
    1)
        echo ""
        echo "📝 Personal Access Token配置说明:"
        echo "1. 访问: https://github.com/settings/tokens"
        echo "2. 点击 'Generate new token (classic)'"
        echo "3. 设置名称: CET4-Learning-System-$(date +%Y%m%d)"
        echo "4. 选择权限:"
        echo "   ✅ repo (完整仓库访问)"
        echo "   ✅ workflow (GitHub Actions)"
        echo "   ✅ write:packages (可选)"
        echo "5. 点击 'Generate token' 并复制token"
        echo ""
        
        read -p "请输入您的Personal Access Token: " -s github_token
        echo ""
        
        if [ -z "$github_token" ]; then
            echo "❌ Token不能为空"
            exit 1
        fi
        
        # 验证token
        echo "🔍 验证Token有效性..."
        response=$(curl -s -w "%{http_code}" -H "Authorization: token $github_token" https://api.github.com/user)
        http_code="${response: -3}"
        
        if [ "$http_code" = "200" ]; then
            echo "✅ Token验证成功"
            
            # 配置远程仓库使用token
            git remote set-url origin "https://$github_token@github.com/ailyedu2030/CET.git"
            echo "✅ 远程仓库已配置使用Token"
            
            # 推送代码
            echo ""
            echo "📤 推送代码到GitHub..."
            if git push -u origin main; then
                echo "✅ 代码推送成功!"
                echo "🌐 仓库地址: https://github.com/ailyedu2030/CET"
                
                # 恢复原始URL（不包含token）
                git remote set-url origin "https://github.com/ailyedu2030/CET.git"
                echo "✅ 远程仓库URL已清理"
            else
                echo "❌ 代码推送失败"
                # 恢复原始URL
                git remote set-url origin "https://github.com/ailyedu2030/CET.git"
                exit 1
            fi
        else
            echo "❌ Token验证失败 (HTTP $http_code)"
            echo "请检查Token是否正确或权限是否足够"
            exit 1
        fi
        ;;
    2)
        echo "🔍 尝试使用现有凭据推送..."
        if git push -u origin main; then
            echo "✅ 代码推送成功!"
            echo "🌐 仓库地址: https://github.com/ailyedu2030/CET"
        else
            echo "❌ 推送失败，请选择其他认证方式"
            exit 1
        fi
        ;;
    3)
        echo "🔑 SSH密钥配置..."
        echo "当前SSH公钥:"
        if [ -f ~/.ssh/id_ed25519.pub ]; then
            cat ~/.ssh/id_ed25519.pub
        elif [ -f ~/.ssh/id_rsa.pub ]; then
            cat ~/.ssh/id_rsa.pub
        else
            echo "❌ 未找到SSH密钥，请先生成:"
            echo "ssh-keygen -t ed25519 -C 'ailyedu@outlook.com'"
            exit 1
        fi
        
        echo ""
        echo "请将上述公钥添加到GitHub:"
        echo "https://github.com/settings/ssh/new"
        echo ""
        read -p "SSH密钥已添加? (y/n): " ssh_added
        
        if [ "$ssh_added" = "y" ]; then
            # 更改为SSH URL
            git remote set-url origin git@github.com:ailyedu2030/CET.git
            
            # 测试SSH连接
            if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
                echo "✅ SSH连接成功"
                
                # 推送代码
                if git push -u origin main; then
                    echo "✅ 代码推送成功!"
                    echo "🌐 仓库地址: https://github.com/ailyedu2030/CET"
                else
                    echo "❌ 代码推送失败"
                    exit 1
                fi
            else
                echo "❌ SSH连接失败"
                exit 1
            fi
        else
            echo "❌ 请先添加SSH密钥"
            exit 1
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 推送完成!"
echo "=================================="
echo "✅ 代码已成功推送到GitHub"
echo "📊 推送统计:"
echo "   - 文件数: $(git ls-files | wc -l)"
echo "   - 提交数: $(git rev-list --count HEAD)"
echo "   - 分支: $(git branch --show-current)"
echo ""
echo "🔗 下一步:"
echo "1. 访问仓库: https://github.com/ailyedu2030/CET"
echo "2. 检查GitHub Actions是否运行"
echo "3. 配置GitHub Secrets"
echo "4. 验证CI/CD流程"
