# 🔧 GitHub配置说明

本目录包含CET4学习系统的GitHub配置文件，用于自动化代码质量检查、持续集成和部署。

## 📁 目录结构

```
.github/
├── workflows/              # GitHub Actions工作流
│   ├── ci.yml              # 持续集成
│   ├── cd.yml              # 持续部署
│   ├── quality-check.yml   # 代码质量检查
│   └── dependency-update.yml # 依赖更新
├── scripts/                # 自动化脚本
│   ├── quality-report.py   # 质量报告生成器
│   ├── deploy.sh          # 部署脚本
│   └── test.sh            # 测试脚本
├── ISSUE_TEMPLATE/         # Issue模板
│   └── code-quality.md    # 代码质量问题模板
├── CODEOWNERS             # 代码所有者配置
├── pull_request_template.md # PR模板
└── README.md              # 本文件
```

## 🚀 工作流说明

### 1. 持续集成 (ci.yml)

**触发条件**:
- 推送到 `main` 或 `develop` 分支
- 创建Pull Request
- 手动触发

**检查内容**:
- ✅ Python代码质量 (Ruff + MyPy)
- ✅ 前端代码质量 (ESLint + TypeScript)
- ✅ 单元测试和覆盖率
- ✅ Docker构建测试
- ✅ 安全扫描

### 2. 代码质量检查 (quality-check.yml)

**触发条件**:
- 推送到主要分支
- 每天凌晨2点自动运行
- 手动触发

**检查内容**:
- 🔍 深度代码分析
- 🔒 安全漏洞扫描
- 📊 代码复杂度分析
- 🧹 死代码检测
- 📈 质量趋势分析

### 3. 持续部署 (cd.yml)

**触发条件**:
- 推送到 `main` 分支
- 创建版本标签
- 手动触发

**部署流程**:
- 🏗️ 构建Docker镜像
- 🚀 部署到测试环境
- ✅ 自动化测试验证
- 🎯 部署到生产环境 (需要审批)

### 4. 依赖更新 (dependency-update.yml)

**触发条件**:
- 每周一凌晨2点自动运行
- 手动触发

**更新内容**:
- 📦 Python依赖安全检查
- 🔍 Node.js依赖审计
- 🔄 自动创建更新PR

## 🛠️ 本地开发工具

### 代码质量检查脚本

运行完整的本地质量检查：

```bash
# 运行本地质量检查
./scripts/quality-check-local.sh
```

### Pre-commit Hooks

安装pre-commit hooks：

```bash
# 安装pre-commit
pip install pre-commit

# 安装hooks
pre-commit install

# 手动运行所有hooks
pre-commit run --all-files
```

## 📋 代码质量标准

### Python代码

- ✅ **Ruff**: 零错误零警告
- ✅ **MyPy**: 完整类型注解
- ✅ **格式化**: 使用Ruff格式化
- ✅ **安全**: Bandit扫描通过
- ✅ **测试覆盖率**: ≥80%

### 前端代码

- ✅ **ESLint**: 零错误零警告
- ✅ **TypeScript**: 严格类型检查
- ✅ **格式化**: Prettier格式化
- ✅ **测试覆盖率**: ≥70%

## 🔒 安全配置

### 必需的GitHub Secrets

**测试环境**:
- `STAGING_HOST` - 测试服务器地址
- `STAGING_USER` - 测试服务器用户名
- `STAGING_SSH_KEY` - SSH私钥
- `STAGING_POSTGRES_PASSWORD` - 数据库密码
- `STAGING_REDIS_PASSWORD` - Redis密码

**生产环境**:
- `PROD_HOST` - 生产服务器地址
- `PROD_USER` - 生产服务器用户名
- `PROD_SSH_KEY` - SSH私钥
- `PROD_POSTGRES_PASSWORD` - 数据库密码
- `PROD_REDIS_PASSWORD` - Redis密码

**通用配置**:
- `DEEPSEEK_API_KEYS` - AI服务API密钥
- `SLACK_WEBHOOK` - Slack通知webhook

## 📊 质量报告

### 自动生成报告

每次质量检查后会自动生成：
- 📄 Markdown格式报告
- 📊 JSON格式详细数据
- 📈 质量趋势图表

### 报告内容

- 代码质量评分
- 安全问题统计
- 复杂度分析
- 测试覆盖率
- 改进建议

## 🔄 工作流程

### 开发流程

1. **创建分支**: 从 `develop` 创建功能分支
2. **本地开发**: 使用本地质量检查脚本
3. **提交代码**: Pre-commit hooks自动检查
4. **创建PR**: 使用PR模板
5. **CI检查**: 自动运行所有检查
6. **代码审查**: 根据CODEOWNERS配置
7. **合并代码**: 所有检查通过后合并

### 发布流程

1. **合并到main**: 触发部署到测试环境
2. **测试验证**: 自动化测试验证
3. **创建标签**: 创建版本标签
4. **生产部署**: 需要手动审批
5. **监控验证**: 部署后监控检查

## 🆘 故障排除

### 常见问题

**CI失败**:
1. 检查代码质量问题
2. 运行本地质量检查脚本
3. 修复所有问题后重新提交

**部署失败**:
1. 检查服务器连接
2. 验证环境变量配置
3. 查看部署日志

**依赖问题**:
1. 检查requirements.txt
2. 运行依赖安全扫描
3. 更新有漏洞的依赖

## 📞 支持

如有问题，请：
1. 查看工作流日志
2. 创建Issue使用相应模板
3. 联系相关团队 (参考CODEOWNERS)

---

*此配置确保CET4学习系统的代码质量和部署安全性*
