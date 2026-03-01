# CET 项目 Agents 指南

## 项目概述

CET (Coding Education Technology) 是一个教育技术平台，用于代码教育。

## 技术栈

- **后端**: Python FastAPI
- **前端**: React/TypeScript
- **数据库**: PostgreSQL (通过 Alembic 管理)
- **容器**: Docker, Docker Compose
- **测试**: pytest

## 目录结构

```
/app                 # 主应用代码
  /api              # API 路由
  /core             # 核心配置
  /models           # 数据库模型
  /schemas          # Pydantic schemas
  /services         # 业务逻辑
  /utils            # 工具函数
/alembic            # 数据库迁移
/frontend           # 前端代码
/config             # 配置文件
/scripts            # 脚本
/tests              # 测试
```

## 代码规范

- 使用 Python type hints
- 遵循 PEP 8
- 使用 Pydantic 进行数据验证
- 使用 SQLAlchemy 作为 ORM

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行后端
uvicorn app.main:app --reload

# 运行测试
pytest

# 数据库迁移
alembic upgrade head
```

## Agents 使用

### 正确的调用方式

这些是 **Agents（智能体）**，不是 slash 命令。需要通过 `task()` 或 `call_omo_agent()` 调用：

```typescript
// ✅ 正确的方式 - 使用 task() 调用
task(
  subagent_type="code-reviewer", 
  prompt="请审查这段代码: ...", 
  load_skills=[]
)

// ✅ 正确的方式 - 使用 call_omo_agent()
call_omo_agent(
  subagent_type="build-error-resolver", 
  prompt="修复这个构建错误: ..."
)
```

### ❌ 错误的调用方式

```typescript
// ❌ 错误 - 这些是 agents，不是 skills
skill("code-reviewer")
load_skills: ["build-error-resolver"]

// ❌ 错误 - 不是 slash 命令
/code-reviewer
/build-error-resolver
```

### 可用的 Specialized Agents

| Agent | 用途 |
|-------|------|
| `code-reviewer` | 代码审查 |
| `security-reviewer` | 安全审查 |
| `python-reviewer` | Python 专项审查 |
| `database-reviewer` | 数据库审查 |
| `go-reviewer` | Go 代码审查 |
| `tdd-guide` | TDD 指导 |
| `e2e-runner` | E2E 测试 |
| `refactor-cleaner` | 重构 |
| `build-error-resolver` | 构建错误修复 |
| `doc-updater` | 文档更新 |

### 可用的 Built-in Agents

| Agent | 用途 |
|-------|------|
| `sisyphus` | 主编排器 |
| `hephaestus` | 深度工作 |
| `oracle` | 顾问（只读）|
| `atlas` | Todo 编排 |
| `prometheus` | 规划 |
| `metis` | 计划咨询 |
| `momus` | 计划审查 |
| `librarian` | 文档搜索 |
| `explore` | 代码搜索 |
| `multimodal-looker` | 图片/PDF 分析 |

### 可用的 Skills

| Skill | 用途 |
|-------|------|
| `git-master` | Git 操作 |
| `playwright` | 浏览器自动化 |
| `frontend-ui-ux` | 前端 UI/UX |
| `dev-browser` | 浏览器交互 |

使用方式：
```typescript
task(
  category="visual-engineering", 
  load_skills=["frontend-ui-ux"],
  prompt="..."
)
```
