# 英语四级学习及教学系统

## 项目概述

本系统是一个基于AI驱动的英语四级学习及教学平台，采用单体架构模块化设计，为管理员、教师和学生提供完整的教学管理和学习训练解决方案。

### 核心特性

- 🤖 **AI智能批改**：基于DeepSeek引擎的智能批改系统，准确率>90%
- 📊 **智能训练闭环**：学生训练→AI分析→教师调整→内容优化的完整闭环
- 🎯 **个性化学习**：自适应难度调整，个性化内容推荐
- 📚 **资源库管理**：大规模文档处理，向量检索，语义搜索
- 🔒 **安全可靠**：完整的安全防护，数据加密，权限控制
- 📈 **实时监控**：系统监控，性能分析，智能告警

## 技术架构

### 后端技术栈
- **应用框架**：FastAPI 0.104+ (Python 3.11+)
- **数据库**：PostgreSQL 15 (主业务数据)
- **缓存**：Redis 7 (会话、缓存、队列)
- **向量数据库**：Milvus 2.3+ (文档检索)
- **对象存储**：MinIO (文件存储)
- **任务队列**：Celery + Redis
- **ORM**：SQLAlchemy 2.0 + Alembic

### 前端技术栈
- **框架**：React 18.x + TypeScript 5.x
- **构建工具**：Vite 5.x
- **UI组件**：Mantine 7.x
- **状态管理**：Zustand 4.x
- **HTTP客户端**：TanStack Query 5.x
- **路由**：React Router 6.x

### 基础设施
- **容器化**：Docker + Docker Compose
- **Web服务器**：Nginx (反向代理)
- **监控**：Prometheus + Grafana
- **日志**：结构化日志 (Loguru)

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7

### 安装依赖

#### 后端依赖
```bash
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
```

### 开发环境启动

#### 1. 启动数据库服务
```bash
docker-compose up -d postgres redis milvus minio
```

#### 2. 数据库迁移
```bash
alembic upgrade head
```

#### 3. 启动后端服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. 启动前端服务
```bash
cd frontend
npm run dev
```

### 生产环境部署

#### 使用Docker Compose一键部署
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 项目结构

```
/
├── app/                        # 后端应用
│   ├── main.py                 # FastAPI应用入口
│   ├── core/                   # 核心配置
│   ├── users/                  # 用户管理模块
│   ├── courses/                # 课程管理模块
│   ├── training/               # 训练系统模块
│   ├── ai/                     # AI集成模块
│   ├── notifications/          # 通知系统模块
│   ├── analytics/              # 数据分析模块
│   ├── resources/              # 资源库模块
│   └── shared/                 # 共享组件
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   ├── pages/              # 页面组件
│   │   ├── stores/             # 状态管理
│   │   ├── api/                # API调用
│   │   └── utils/              # 工具函数
│   └── public/                 # 静态资源
├── tests/                      # 测试目录
├── docs/                       # 项目文档
├── scripts/                    # 构建和部署脚本
├── docker-compose.yml          # Docker编排
└── requirements.txt            # Python依赖
```

## 开发规范

### 代码质量
- **Python**：使用Ruff + mypy，零容忍linter错误
- **TypeScript**：使用tsc + ESLint，零容忍linter错误
- **测试覆盖**：单元测试>80%，集成测试>70%
- **API文档**：自动生成OpenAPI文档

### 提交规范
```bash
# 代码质量检查
ruff check .
mypy .
cd frontend && npm run lint && npm run type-check

# 运行测试
pytest tests/
cd frontend && npm test

# 提交代码
git add .
git commit -m "feat: 添加新功能"
git push
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 监控面板

- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## 许可证

MIT License

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 联系我们

- 项目主页：https://github.com/cet4-learning/system
- 问题反馈：https://github.com/cet4-learning/system/issues
- 邮箱：team@cet4learning.com

---

**注意**：本项目采用AI驱动开发，一次成型交付，代码质量达到生产级标准。