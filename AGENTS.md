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

所有 oh-my-opencode 的 specialized agents 都可以通过以下方式使用：
- `code-reviewer` - 代码审查
- `security-reviewer` - 安全审查
- `python-reviewer` - Python 专项审查
- `tdd-guide` - TDD 指导
- `e2e-runner` - E2E 测试
- `refactor-cleaner` - 重构
- `build-error-resolver` - 构建错误修复
- `doc-updater` - 文档更新
