#!/bin/bash

# GitHub认证配置脚本
# 用于配置Personal Access Token和推送代码

set -e

echo "🔐 GitHub认证配置向导"
echo "=================================="

# 检查当前Git配置
echo "📋 当前Git配置:"
echo "用户名: $(git config user.name)"
echo "邮箱: $(git config user.email)"
echo "远程仓库: $(git remote get-url origin 2>/dev/null || echo '未配置')"
echo ""

# 检查GitHub CLI状态
echo "🔍 检查GitHub CLI状态..."
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI已安装"
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI已认证"
        echo "当前用户: $(gh api user --jq .login)"
    else
        echo "⚠️  GitHub CLI未认证"
    fi
else
    echo "❌ GitHub CLI未安装"
fi
echo ""

echo "🎯 认证方案选择:"
echo "1. 使用GitHub CLI认证（推荐）"
echo "2. 使用Personal Access Token"
echo "3. 使用SSH密钥"
echo ""

read -p "请选择认证方案 (1-3): " auth_choice

case $auth_choice in
    1)
        echo "🔑 使用GitHub CLI认证..."
        if command -v gh &> /dev/null; then
            echo "正在启动GitHub CLI认证流程..."
            gh auth login --web --git-protocol https
            
            # 验证认证
            if gh auth status &> /dev/null; then
                echo "✅ GitHub CLI认证成功"
                echo "当前用户: $(gh api user --jq .login)"
                
                # 配置Git使用GitHub CLI
                gh auth setup-git
                echo "✅ Git已配置使用GitHub CLI认证"
            else
                echo "❌ GitHub CLI认证失败"
                exit 1
            fi
        else
            echo "❌ GitHub CLI未安装，请先安装: brew install gh"
            exit 1
        fi
        ;;
    2)
        echo "🔑 使用Personal Access Token..."
        echo ""
        echo "📝 请按以下步骤创建Personal Access Token:"
        echo "1. 访问: https://github.com/settings/tokens"
        echo "2. 点击 'Generate new token (classic)'"
        echo "3. 设置Token名称: CET4-Learning-System"
        echo "4. 选择权限范围:"
        echo "   ✅ repo (完整仓库访问)"
        echo "   ✅ workflow (GitHub Actions)"
        echo "   ✅ write:packages (包发布)"
        echo "   ✅ delete_repo (删除仓库，可选)"
        echo "5. 点击 'Generate token'"
        echo "6. 复制生成的token"
        echo ""
        
        read -p "请输入您的Personal Access Token: " -s token
        echo ""
        
        if [ -z "$token" ]; then
            echo "❌ Token不能为空"
            exit 1
        fi
        
        # 验证token
        echo "🔍 验证Token..."
        if curl -s -H "Authorization: token $token" https://api.github.com/user | grep -q "login"; then
            echo "✅ Token验证成功"
            
            # 配置Git使用token
            git remote set-url origin "https://$token@github.com/ailyedu2030/CET.git"
            echo "✅ Git远程仓库已配置使用Token"
            
            # 保存token到Git配置（可选）
            read -p "是否保存Token到Git配置? (y/n): " save_token
            if [ "$save_token" = "y" ]; then
                git config credential.helper store
                echo "✅ Token已保存到Git凭据存储"
            fi
        else
            echo "❌ Token验证失败，请检查Token是否正确"
            exit 1
        fi
        ;;
    3)
        echo "🔑 使用SSH密钥..."
        
        # 检查是否已有SSH密钥
        if [ -f ~/.ssh/id_rsa.pub ] || [ -f ~/.ssh/id_ed25519.pub ]; then
            echo "✅ 发现现有SSH密钥"
            if [ -f ~/.ssh/id_ed25519.pub ]; then
                echo "公钥内容:"
                cat ~/.ssh/id_ed25519.pub
            elif [ -f ~/.ssh/id_rsa.pub ]; then
                echo "公钥内容:"
                cat ~/.ssh/id_rsa.pub
            fi
        else
            echo "📝 生成新的SSH密钥..."
            read -p "请输入您的GitHub邮箱: " email
            ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
            echo "✅ SSH密钥已生成"
            echo "公钥内容:"
            cat ~/.ssh/id_ed25519.pub
        fi
        
        echo ""
        echo "📝 请按以下步骤添加SSH密钥到GitHub:"
        echo "1. 复制上面显示的公钥内容"
        echo "2. 访问: https://github.com/settings/ssh/new"
        echo "3. 设置标题: CET4-Learning-System"
        echo "4. 粘贴公钥内容"
        echo "5. 点击 'Add SSH key'"
        echo ""
        
        read -p "SSH密钥已添加到GitHub? (y/n): " ssh_added
        if [ "$ssh_added" = "y" ]; then
            # 测试SSH连接
            echo "🔍 测试SSH连接..."
            if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
                echo "✅ SSH连接测试成功"
                
                # 更新远程仓库URL为SSH
                git remote set-url origin git@github.com:ailyedu2030/CET.git
                echo "✅ Git远程仓库已配置使用SSH"
            else
                echo "❌ SSH连接测试失败"
                exit 1
            fi
        else
            echo "❌ 请先添加SSH密钥到GitHub"
            exit 1
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🚀 准备推送代码到GitHub..."
echo "远程仓库: $(git remote get-url origin)"
echo "当前分支: $(git branch --show-current)"
echo "提交数量: $(git rev-list --count HEAD)"

read -p "是否现在推送代码到GitHub? (y/n): " push_now
if [ "$push_now" = "y" ]; then
    echo "📤 推送代码到GitHub..."
    if git push -u origin main; then
        echo "✅ 代码推送成功!"
        echo "🌐 仓库地址: https://github.com/ailyedu2030/CET"
    else
        echo "❌ 代码推送失败"
        exit 1
    fi
else
    echo "⏸️  稍后可使用以下命令推送:"
    echo "   git push -u origin main"
fi

echo ""
echo "=================================="
echo "✅ GitHub认证配置完成!"
