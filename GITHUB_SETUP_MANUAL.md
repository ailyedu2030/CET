# 🚀 GitHub手动配置指南

## 📋 当前状态确认

✅ **本地Git仓库已准备就绪**
- 项目目录: `/Volumes/APP1/CET`
- Git状态: 已初始化，包含2个提交
- 文件数量: 608个文件，267,390行代码
- 当前分支: `main`
- 备份状态: 已完成3种备份（完整目录、Git存档、质量报告）

## 🎯 需要完成的步骤

### 第一步：在GitHub上创建仓库

1. **访问GitHub创建仓库页面**
   ```
   https://github.com/new
   ```

2. **填写仓库信息**
   - Repository name: `CET`
   - Description: `CET4 Learning System - AI-powered English learning platform with comprehensive training modules, adaptive learning algorithms, and intelligent teaching assistance.`
   - Visibility: `Public` (推荐) 或 `Private`
   - ❌ **不要**勾选 "Add a README file"
   - ❌ **不要**勾选 "Add .gitignore"
   - ❌ **不要**勾选 "Choose a license"

3. **点击 "Create repository"**

### 第二步：获取Personal Access Token

1. **访问GitHub Token设置页面**
   ```
   https://github.com/settings/tokens
   ```

2. **创建新Token**
   - 点击 "Generate new token (classic)"
   - Token name: `CET4-Learning-System-2025`
   - Expiration: `90 days` (或根据需要选择)
   - 选择权限范围:
     - ✅ `repo` (完整仓库访问)
     - ✅ `workflow` (GitHub Actions)
     - ✅ `write:packages` (可选，用于包发布)

3. **生成并复制Token**
   - 点击 "Generate token"
   - **立即复制Token** (只显示一次)

### 第三步：推送代码到GitHub

1. **使用提供的推送脚本**
   ```bash
   cd /Volumes/APP1/CET
   ./scripts/github-push-with-token.sh
   ```
   
   或者手动执行以下命令：

2. **手动推送步骤**
   ```bash
   # 1. 确认远程仓库配置
   git remote -v
   
   # 2. 如果需要，更新远程仓库URL
   git remote set-url origin https://github.com/ailyedu2030/CET.git
   
   # 3. 使用Token推送（将YOUR_TOKEN替换为实际token）
   git remote set-url origin https://YOUR_TOKEN@github.com/ailyedu2030/CET.git
   git push -u origin main
   
   # 4. 推送成功后，清理URL中的token
   git remote set-url origin https://github.com/ailyedu2030/CET.git
   ```

### 第四步：验证推送结果

1. **访问仓库页面**
   ```
   https://github.com/ailyedu2030/CET
   ```

2. **检查内容**
   - ✅ 确认所有文件已上传
   - ✅ 确认README.md显示正常
   - ✅ 确认.github/workflows目录存在

## 🔧 GitHub Secrets配置

推送成功后，需要配置以下Secrets用于CI/CD：

### 访问Secrets设置页面
```
https://github.com/ailyedu2030/CET/settings/secrets/actions
```

### 必需的Secrets

#### 🔑 **API密钥**
```
DEEPSEEK_API_KEYS
值: your-deepseek-api-keys (多个用逗号分隔)
```

#### 🚀 **部署配置**
```
# 测试环境
STAGING_HOST=your-staging-server.com
STAGING_USER=deploy
STAGING_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...
STAGING_POSTGRES_PASSWORD=secure-password
STAGING_REDIS_PASSWORD=secure-password

# 生产环境
PROD_HOST=your-production-server.com
PROD_USER=deploy
PROD_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...
PROD_POSTGRES_PASSWORD=secure-password
PROD_REDIS_PASSWORD=secure-password
```

#### 📢 **通知配置**
```
SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

## 🔍 验证GitHub Actions

### 检查工作流状态

1. **访问Actions页面**
   ```
   https://github.com/ailyedu2030/CET/actions
   ```

2. **预期的工作流**
   - ✅ `CI` - 持续集成
   - ✅ `Quality Check` - 代码质量检查
   - ✅ `Dependency Update` - 依赖更新检查

3. **首次推送触发**
   - CI工作流应该自动运行
   - 检查是否有任何失败的步骤

### 工作流文件位置
```
.github/workflows/ci.yml
.github/workflows/quality-check.yml
.github/workflows/cd.yml
.github/workflows/dependency-update.yml
```

## 🛡️ 验证GitHub集成功能

### 1. CODEOWNERS功能
- 创建一个测试PR
- 检查是否自动分配审查者

### 2. PR模板
- 创建新PR时应显示模板内容
- 位置: `.github/pull_request_template.md`

### 3. Issue模板
- 创建新Issue时应显示模板选项
- 位置: `.github/ISSUE_TEMPLATE/`

## 🚨 故障排除

### 推送失败常见问题

1. **认证失败**
   - 检查Token权限
   - 确认Token未过期
   - 验证仓库名称正确

2. **网络问题**
   - 检查代理设置
   - 尝试不同的网络环境

3. **仓库不存在**
   - 确认在GitHub上创建了仓库
   - 检查仓库名称大小写

### GitHub Actions失败

1. **Secrets未配置**
   - 检查必需的Secrets是否已添加
   - 验证Secrets值的格式

2. **权限问题**
   - 确认Token有workflow权限
   - 检查仓库设置中的Actions权限

## 📞 获取帮助

如果遇到问题，可以：

1. **检查日志**
   - Git操作日志
   - GitHub Actions日志

2. **参考文档**
   - `.github/README.md`
   - `GITHUB_SETUP_COMPLETE.md`

3. **使用备份**
   - 完整目录备份: `/Volumes/APP1/CET_backup_*`
   - Git存档备份: `/Volumes/APP1/CET_git_archive_*.tar.gz`

---

**🎯 目标：完成GitHub集成，启用完整的CI/CD流程**
