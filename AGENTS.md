# CET 教育平台项目

## 项目概述
CET 教育平台是一个基于 FastAPI 的英语水平考试训练系统，提供词汇、听力、阅读、写作、翻译等训练模块。

## 技术栈
- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **前端**: React + TypeScript
- **AI**: OpenAI GPT API
- **数据库**: PostgreSQL + Redis
- **向量数据库**: Milvus

## 核心模块

### app/training/
- `services/achievement_service.py` - 成就系统
- `services/goal_setting_service.py` - 目标设定
- `services/learning_plan_service.py` - 学习计划
- `services/progress_monitoring_service.py` - 进度监控
- `services/error_analysis_service.py` - 错题分析
- `services/competition_service.py` - 竞赛系统
- `services/social_learning_service.py` - 社交学习

### app/users/
- `services/auth_service.py` - 认证服务
- `services/admin_service.py` - 管理服务

### app/resources/
- `services/permission_service.py` - 权限服务
- `services/knowledge_service.py` - 知识服务

## 代码规范
- 使用 async/await 异步编程
- 遵循 PEP 8 代码规范
- 使用 Pydantic 进行数据验证
- 所有服务方法必须包含完整的异常处理

## 数据库模型
- TrainingSessionModel - 训练会话
- TrainingGoalModel - 学习目标
- LearningPlanModel - 学习计划
- StudyGroupModel - 学习小组
- AchievementModel - 成就
