# CET 项目全量功能审计报告

> 文档版本: 1.0  
> 创建日期: 2026-03-03  
> 目的: 为全新重构到 Supabase + Next.js 提供完整功能清单

---

## 一、项目概述

### 1.1 技术栈

| 层级 | 当前技术 | 目标技术 (推荐) |
|------|---------|---------------|
| 前端 | React 18 + Vite + Mantine | Next.js 15 + shadcn/ui + Tailwind |
| 后端 | FastAPI + SQLAlchemy | Supabase (BaaS) + FastAPI (仅 AI) |
| 数据库 | PostgreSQL + Redis + Milvus | PostgreSQL + pgvector |
| AI | DeepSeek API | DeepSeek API (保留) |
| 部署 | Docker | Vercel + Supabase |

### 1.2 项目规模

| 指标 | 数量 |
|------|------|
| 后端 API 端点 | 50+ |
| 后端 Services | 137 |
| 前端页面 | 56+ |
| 前端 API 客户端 | 40 |
| 前端 Components | 20+ |
| 总功能点 | 300+ |

---

## 二、后端功能详细清单

### 2.1 用户模块 (users)

#### 2.1.1 API 端点 (15个)

| 文件 | 功能 | 迁移优先级 |
|------|------|-----------|
| `auth_endpoints.py` | 登录、登出、Token刷新、MFA | P0 |
| `registration_endpoints.py` | 用户注册 | P0 |
| `admin_endpoints.py` | 管理员操作 | P0 |
| `mfa_endpoints.py` | 多因素认证 | P1 |
| `permission_endpoints.py` | 权限管理 | P0 |
| `audit_endpoints.py` | 审计日志 | P1 |
| `activation_endpoints.py` | 账户激活 | P1 |
| `registration_verification_endpoints.py` | 注册验证 | P1 |
| `backup_endpoints.py` | 备份管理 | P2 |
| `backup_permissions_endpoints.py` | 备份权限 | P2 |
| `restore_endpoints.py` | 恢复操作 | P2 |
| `security_endpoints.py` | 安全设置 | P1 |
| `teacher_notifications_endpoints.py` | 教师通知 | P1 |
| `basic_info_endpoints.py` | 基本信息 | P1 |
| `permission_endpoints.py` | 权限端点 | P0 |

#### 2.1.2 Services (13个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `auth_service.py` | 认证核心逻辑 | P0 |
| `registration_service.py` | 注册服务 | P0 |
| `admin_service.py` | 管理员服务 | P0 |
| `mfa_service.py` | MFA服务 | P1 |
| `permission_service.py` | 权限服务 | P0 |
| `audit_service.py` | 审计服务 | P1 |
| `activation_service.py` | 激活服务 | P1 |
| `registration_verification_service.py` | 注册验证 | P1 |
| `profile_service.py` | 用户资料 | P1 |
| `token_blocklist_service.py` | Token黑名单 | P0 |

---

### 2.2 训练模块 (training) - 核心业务

#### 2.2.1 API 端点 (12个)

| 文件 | 功能 | 迁移优先级 |
|------|------|-----------|
| `training_center_endpoints.py` | 训练中心 | P0 |
| `listening_endpoints.py` | 听力训练 | P0 |
| `reading_endpoints.py` | 阅读理解 | P0 |
| `writing_endpoints.py` | 写作训练 | P0 |
| `adaptive_learning_endpoints.py` | 自适应学习 | P0 |
| `learning_plan_endpoints.py` | 学习计划 | P0 |
| `learning_management_endpoints.py` | 学习管理 | P1 |
| `training_workshop_endpoints.py` | 训练工坊 | P1 |
| `assistant_endpoints.py` | AI助手 | P1 |
| `social_endpoints.py` | 社交学习 | P2 |
| `social_interaction_endpoints.py` | 社交互动 | P2 |
| `training_endpoints.py` | 训练通用 | P0 |

#### 2.2.2 Services (27个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `training_center_service.py` | 综合训练中心 | P0 |
| `listening_service.py` | 听力训练 | P0 |
| `reading_service.py` | 阅读理解 | P0 |
| `writing_service.py` | 写作训练 | P0 |
| `adaptive_service.py` | 自适应学习 | P0 |
| `personalized_recommendation_service.py` | 个性化推荐 | P0 |
| `progress_monitoring_service.py` | 进度监控 | P0 |
| `achievement_service.py` | 成就系统 | P1 |
| `goal_setting_service.py` | 目标设定 | P1 |
| `learning_plan_service.py` | 学习计划 | P0 |
| `error_analysis_service.py` | 错题分析 | P0 |
| `grading_service.py` | 评分服务 | P0 |
| `competition_service.py` | 竞赛系统 | P2 |
| `social_learning_service.py` | 社交学习 | P2 |
| `forgetting_curve_service.py` | 艾宾浩斯遗忘曲线 | P1 |
| `question_batch_service.py` | 题目批处理 | P1 |
| `ai_analysis_service.py` | AI分析 | P0 |
| `assistant_service.py` | AI助手 | P1 |
| `intelligent_training_loop_service.py` | 智能训练循环 | P1 |
| `real_time_monitoring_service.py` | 实时监控 | P2 |

---

### 2.3 AI 模块 (ai) - 核心竞争力

#### 2.3.1 API 端点 (4个)

| 文件 | 功能 | 迁移优先级 |
|------|------|-----------|
| `ai_endpoints.py` | AI通用接口 | P0 |
| `ai_grading_endpoints.py` | AI批改 | P0 |
| `grading_endpoints.py` | 评分接口 | P0 |
| `enhanced_teaching_endpoints.py` | 增强教学 | P1 |

#### 2.3.2 Services (18个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `deepseek_service.py` | DeepSeek AI集成 | P0 |
| `deepseek_content_service.py` | 内容生成 | P0 |
| `deepseek_embedding_service.py` | 向量嵌入 | P1 |
| `grading_service.py` | 作文/翻译批改 | P0 |
| `lesson_plan_service.py` | AI教案生成 | P0 |
| `syllabus_service.py` | AI大纲生成 | P0 |
| `learning_adjustment_service.py` | AI教学调整 | P0 |
| `enhanced_learning_analytics.py` | AI学习分析 | P0 |
| `content_security_service.py` | 内容安全审核 | P1 |
| `api_key_pool_service.py` | API密钥池 | P1 |
| `optimized_recommendation_engine.py` | 推荐引擎 | P0 |
| `enhanced_collaboration_manager.py` | 协作管理 | P2 |
| `cost_optimization_service.py` | 成本优化 | P2 |
| `quality_monitoring_service.py` | 质量监控 | P2 |
| `fallback_service.py` | 降级服务 | P1 |
| `intelligent_teaching_adjustment.py` | 智能教学调整 | P0 |

---

### 2.4 课程模块 (courses)

#### 2.4.1 API 端点 (7个)

| 文件 | 功能 | 迁移优先级 |
|------|------|-----------|
| `course_endpoints.py` | 课程管理 | P0 |
| `class_endpoints.py` | 班级管理 | P1 |
| `class_management_endpoints.py` | 班级运营 | P1 |
| `assignment_endpoints.py` | 作业管理 | P1 |
| `course_assignment_endpoints.py` | 课程作业 | P1 |
| `rule_endpoints.py` | 规则管理 | P2 |
| `syllabus_approval_endpoints.py` | 大纲审批 | P1 |

#### 2.4.2 Services (8个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `course_service.py` | 课程服务 | P0 |
| `class_service.py` | 班级服务 | P1 |
| `class_management_service.py` | 班级运营 | P1 |
| `assignment_service.py` | 作业服务 | P1 |
| `course_assignment_service.py` | 课程作业 | P1 |
| `course_lifecycle_service.py` | 课程生命周期 | P1 |
| `rule_management_service.py` | 规则管理 | P2 |
| `template_service.py` | 模板服务 | P2 |

---

### 2.5 分析模块 (analytics)

#### 2.5.1 API 端点 (5个)

| 文件 | 功能 | 迁移优先级 |
|------|------|-----------|
| `system_monitoring_endpoints.py` | 系统监控 | P1 |
| `report_generation_endpoints.py` | 报表生成 | P1 |
| `data_visualization_endpoints.py` | 数据可视化 | P1 |
| `enhanced_monitoring_endpoints.py` | 增强监控 | P2 |
| `alert_management_endpoints.py` | 告警管理 | P2 |

#### 2.5.2 Services (10个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `system_monitoring_service.py` | 系统监控 | P1 |
| `learning_analytics_service.py` | 学习分析 | P1 |
| `report_service.py` | 报表服务 | P1 |
| `enhanced_performance_monitor.py` | 性能监控 | P2 |
| `intelligent_alert_manager.py` | 智能告警 | P2 |
| `prediction_service.py` | 预测服务 | P2 |
| `teaching_effectiveness_service.py` | 教学效果 | P2 |
| `custom_report_service.py` | 自定义报表 | P2 |

---

### 2.6 资源模块 (resources)

#### 2.6.1 API 端点 (5个)

| 文件 | 功能 | 迁移优先级 |
|------|------|-----------|
| `resource_endpoints.py` | 资源管理 | P1 |
| `course_resource_endpoints.py` | 课程资源 | P1 |
| `hotspot_endpoints.py` | 热点管理 | P2 |
| `permission_endpoints.py` | 权限管理 | P1 |
| `professional_development_endpoints.py` | 专业发展 | P2 |

#### 2.6.2 Services (18个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `resource_library_service.py` | 资源库 | P1 |
| `material_service.py` | 教材服务 | P1 |
| `knowledge_service.py` | 知识服务 | P1 |
| `knowledge_graph_service.py` | 知识图谱 | P2 |
| `vector_search_service.py` | 向量搜索 | P1 |
| `vocabulary_service.py` | 词汇服务 | P0 |
| `semantic_search_service.py` | 语义搜索 | P1 |
| `ocr_service.py` | OCR识别 | P2 |
| `file_processor.py` | 文件处理 | P1 |
| `document_processing_service.py` | 文档处理 | P1 |

---

### 2.7 通知模块 (notifications)

#### 2.7.1 API 端点 (1个)

| 文件 | 功能 | 迁移优先级 |
|------|------|-----------|
| `notification_endpoints.py` | 通知管理 | P1 |

#### 2.7.2 Services (2个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `notification_service.py` | 通知服务 | P1 |
| `websocket_manager.py` | WebSocket管理 | P1 |

---

## 三、前端功能详细清单

### 3.1 Admin 页面 (15个)

| 页面 | 功能 | 迁移优先级 |
|------|------|-----------|
| `AdminCoursesPage.tsx` | 课程管理 | P0 |
| `AdminUsersPage.tsx` | 用户管理 | P0 |
| `AuditLogPage.tsx` | 审计日志 | P1 |
| `BackupManagementPage.tsx` | 备份管理 | P2 |
| `ClassManagementPage.tsx` | 班级管理 | P1 |
| `ClassroomManagementPage.tsx` | 教室管理 | P2 |
| `CourseAssignmentPage.tsx` | 课程分配 | P1 |
| `MFAManagementPage.tsx` | MFA管理 | P1 |
| `PermissionAuditPage.tsx` | 权限审计 | P1 |
| `PermissionManagementPage.tsx` | 权限管理 | P0 |
| `RegistrationReviewPage.tsx` | 注册审核 | P1 |
| `RuleManagementPage.tsx` | 规则管理 | P2 |
| `StudentManagementPage.tsx` | 学生管理 | P0 |
| `SystemMonitoringPage.tsx` | 系统监控 | P1 |
| `TeacherManagementPage.tsx` | 教师管理 | P0 |

### 3.2 Teacher 页面 (19个)

| 页面 | 功能 | 迁移优先级 |
|------|------|-----------|
| `TeacherDashboard.tsx` | 教师仪表盘 | P0 |
| `TeacherCoursesPage.tsx` | 我的课程 | P0 |
| `LessonPlanPage.tsx` | 教案生成 | P0 |
| `SyllabusGeneratorPage.tsx` | 大纲生成 | P0 |
| `IntelligentTeachingWorkbench.tsx` | 智能教学工作台 | P0 |
| `TeachingAdjustmentsPage.tsx` | 教学调整 | P0 |
| `LearningAnalyticsPage.tsx` | 学习分析 | P1 |
| `TrainingWorkshopPage.tsx` | 训练工坊 | P1 |
| `ProfessionalDevelopmentPage.tsx` | 专业发展 | P2 |
| `SchedulePage.tsx` | 日程管理 | P2 |
| `TeacherProfilePage.tsx` | 教师资料 | P1 |
| `TeacherQualificationPage.tsx` | 资格管理 | P2 |
| `TeacherResourcesPage.tsx` | 教学资源 | P1 |
| `HotTopicsPage.tsx` | 热点话题 | P2 |
| `SystemArchitecture.tsx` | 系统架构 | P2 |
| `SystemCoordinationPage.tsx` | 系统协调 | P2 |
| `TechnicalRequirementsPage.tsx` | 技术需求 | P2 |
| `OfflineTest.tsx` | 离线测试 | P2 |
| `PWATest.tsx` | PWA测试 | P2 |

### 3.3 Student 页面 (17+)

| 页面/目录 | 功能 | 迁移优先级 |
|----------|------|-----------|
| `StudentTrainingPage.tsx` | 学习训练 | P0 |
| `TrainingCenter/` | 训练中心 | P0 |
| `ListeningTraining/` | 听力训练 | P0 |
| `Writing/` | 写作训练 | P0 |
| `AdaptiveLearningPage.tsx` | 自适应学习 | P0 |
| `StudentProgressPage.tsx` | 学习进度 | P0 |
| `ErrorReinforcement/` | 错题强化 | P0 |
| `LearningPlan/` | 学习计划 | P0 |
| `GradingResults/` | 批改结果 | P0 |
| `SocialLearning/` | 社交学习 | P2 |
| `SystemStatusPage.tsx` | 系统状态 | P2 |

### 3.4 前端 Services (7个)

| Service | 功能 | 迁移优先级 |
|---------|------|-----------|
| `aiService.ts` | AI服务 | P0 |
| `batchProcessor.ts` | 批处理 | P1 |
| `networkOptimizer.ts` | 网络优化 | P2 |
| `offlineStorage.ts` | 离线存储 | P1 |
| `offlineSync.ts` | 离线同步 | P1 |
| `securityService.ts` | 安全服务 | P1 |
| `smartPreloader.ts` | 智能预加载 | P2 |

### 3.5 前端 API 客户端 (40个)

| API文件 | 功能 | 迁移优先级 |
|--------|------|-----------|
| `auth.ts` | 认证 | P0 |
| `training.ts` | 训练 | P0 |
| `trainingCenter.ts` | 训练中心 | P0 |
| `listening.ts` | 听力 | P0 |
| `reading.ts` | 阅读 | P0 |
| `writing.ts` | 写作 | P0 |
| `adaptiveLearning.ts` | 自适应 | P0 |
| `learningPlan.ts` | 学习计划 | P0 |
| `grading.ts` | 评分 | P0 |
| `progressTracking.ts` | 进度跟踪 | P0 |
| `errorReinforcement.ts` | 错题强化 | P0 |
| `socialLearning.ts` | 社交学习 | P2 |
| `courseResources.ts` | 课程资源 | P1 |
| `notifications.ts` | 通知 | P1 |
| `systemMonitoring.ts` | 系统监控 | P1 |
| `intelligentTeaching.ts` | 智能教学 | P0 |
| `teacherNotification.ts` | 教师通知 | P1 |
| `backup.ts` | 备份 | P2 |
| `classManagement.ts` | 班级管理 | P1 |
| `permissions.ts` | 权限 | P0 |

---

## 四、核心业务功能映射

### 4.1 学习流程

```
用户注册 → 登录 → 选择角色(学生/教师/管理员)
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
 学生流程       教师流程        管理员流程
    │               │               │
    ↓               ↓               ↓
 学习计划     创建课程        用户管理
 词汇训练     发布作业        课程管理
 听力训练     AI教案         权限管理
 阅读训练     教学调整        系统监控
 写作训练     学习分析        数据分析
 AI批改                          ↓
 错题分析     ←─────────────→
 进度追踪
```

### 4.2 AI 能力矩阵

| AI 功能 | 状态 | 迁移说明 |
|--------|------|---------|
| 作文批改 | ✅ | DeepSeek API - 保留 |
| 翻译评分 | ✅ | DeepSeek API - 保留 |
| 个性化推荐 | ✅ | 迁移到 Supabase Functions |
| 教案生成 | ✅ | DeepSeek API - 保留 |
| 大纲生成 | ✅ | DeepSeek API - 保留 |
| 教学调整 | ✅ | 迁移逻辑到前端 |
| 错题分析 | ✅ | 迁移逻辑到前端 |
| 遗忘曲线 | ✅ | 迁移逻辑到前端 |
| 内容审核 | ✅ | 迁移到 Supabase Functions |
| API 密钥池 | ⚠️ | 需要重构 |

---

## 五、迁移优先级分类

### P0 - 必须迁移 (核心功能)

| 模块 | 功能数 |
|------|-------|
| 用户系统 | 15+ |
| 认证授权 | 10+ |
| 训练中心 | 20+ |
| 五大训练 | 4 |
| AI 批改 | 3 |
| 学习计划 | 5 |
| 进度追踪 | 5 |
| 错题分析 | 3 |

### P1 - 重要功能

| 模块 | 功能数 |
|------|-------|
| 课程管理 | 7+ |
| 通知系统 | 2+ |
| 数据分析 | 8+ |
| 资源管理 | 6+ |
| 权限管理 | 5+ |

### P2 - 可选功能

| 模块 | 功能数 |
|------|-------|
| 社交学习 | 4 |
| 竞赛系统 | 1 |
| 备份恢复 | 4 |
| 系统监控 | 5 |

---

## 六、技术债务修复记录 (2026-03-03)

### 6.1 已完成的修复

| 问题 | 修复内容 | 状态 |
|------|---------|------|
| JWT Token 权限丢失 | refresh token 包含完整 user_type 和 roles | ✅ |
| 前端 API 密钥暴露 | 移除 GradingResultsPage.tsx 中的硬编码密钥 | ✅ |
| 空 Except 块 | 180+ 处添加 logger.warning 日志 | ✅ |
| print 改为 logging | 4 处改为 logger | ✅ |
| 配置安全性 | config.py 添加 Field 验证 | ✅ |

### 6.2 验证状态

| 检查项 | 状态 |
|--------|------|
| mypy | ✅ 通过 |
| ESLint | ✅ 通过 |
| TypeScript | ✅ 通过 |

---

## 七、推荐技术选型

### 7.1 前端模板

**首选**: [Razikus/supabase-nextjs-template](https://github.com/razikus/supabase-nextjs-template)

| 指标 | 值 |
|------|-----|
| Stars | 292 ⭐ |
| 技术栈 | Next.js 15 + React 19 + Tailwind + shadcn/ui |
| 功能 | Auth + Storage + RLS + MFA + i18n |
| 移动端 | 赠送 React Native 模板 |

### 7.2 后端架构

```
┌─────────────────────────────────────────────────────────────┐
│                    推荐架构                                   │
├─────────────────────────────────────────────────────────────┤
│  前端: Next.js 15 + shadcn/ui + Tailwind                   │
│    └── Razikus 模板为基础                                    │
├─────────────────────────────────────────────────────────────┤
│  后端: Supabase (BaaS)                                     │
│    ├── Auth (认证/授权)                                      │
│    ├── Database (PostgreSQL + pgvector)                    │
│    ├── Storage (文件/音频)                                  │
│    └── Realtime (实时通知)                                  │
├─────────────────────────────────────────────────────────────┤
│  AI 服务: 保留现有 FastAPI                                  │
│    ├── 作文批改                                             │
│    ├── 口语评测                                             │
│    └── 个性化推荐                                           │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 成本估算

| 方案 | 月成本 | 说明 |
|------|--------|------|
| Supabase Free | $0 | 适合开发/小规模 |
| Supabase Pro | $25 | 1000+ 并发 |
| Vercel | $0-20 | 取决于流量 |

---

## 八、下一步行动

1. **确认功能清单** - 核对是否有遗漏
2. **选择模板** - 确定使用 Razikus 模板
3. **创建项目** - Fork 模板并初始化
4. **数据库设计** - 基于现有模型设计 Supabase Schema
5. **功能迁移** - 按优先级分阶段迁移
6. **AI 集成** - 保留 FastAPI AI 服务
7. **测试验证** - 确保功能完整

---

## 附录

### A. 文件路径映射

| 当前路径 | 说明 |
|---------|------|
| `app/users/` | 用户模块 |
| `app/training/` | 训练模块 |
| `app/ai/` | AI 模块 |
| `app/courses/` | 课程模块 |
| `app/analytics/` | 分析模块 |
| `app/resources/` | 资源模块 |
| `app/notifications/` | 通知模块 |
| `frontend/src/pages/Admin/` | Admin 页面 |
| `frontend/src/pages/Teacher/` | Teacher 页面 |
| `frontend/src/pages/Student/` | Student 页面 |

### B. 联系方式

如有问题，请联系项目负责人。

---

**文档结束**
