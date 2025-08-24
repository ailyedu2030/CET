# core - 扩展规则

## 📋 来源: intelligent-agent-coding-guidelines.md

# 智能体编码指导原则
## 🎯 核心问题解决方案
### 问题描述
### 解决方案概览
## 📁 单体架构模块化规范
### 标准目录结构
```
项目根目录/
├── frontend/                    # 前端应用（React + TypeScript）
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   ├── pages/              # 页面组件
│   │   ├── hooks/              # 自定义Hooks
│   │   ├── stores/             # Zustand状态管理
│   │   ├── api/                # API调用
│   │   └── utils/              # 工具函数
│   └── package.json            # 前端依赖
```
### 模块内部结构
```
app/{module-name}/
├── __init__.py
├── api/                        # API路由
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── {domain}_endpoints.py
├── models/                     # 数据模型⭐
│   ├── __init__.py
│   └── {domain}_models.py
```
## 🚨 智能体编码前置检查清单
### 1. 确定业务领域
```
文件创建前必须回答:
  - 这个文件属于哪个业务领域？
  - 应该放在哪个微服务下？
  - 文件类型是什么？(API/服务/模型/测试/配置)
```
### 2. 模块归属判断
```
用户管理模块 (app/users/):
  关键词: [user_service, authentication, login, register, auth, permission]
  职责: 用户认证、权限管理、用户信息、注册审核

AI集成模块 (app/ai/):
  关键词: [deepseek, openai, ai_service, temperature, llm, gpt, grading]
  职责: AI模型调用、智能分析、内容生成、智能批改

课程管理模块 (app/courses/):
  关键词: [course_service, curriculum, lesson, syllabus, class, teaching]
```
### 3. 文件类型判断
```
API端点文件:
  位置: app/api/v1/
  特征: router, APIRouter, @app.get, @app.post
  命名: {domain}_endpoints.py

业务服务文件:
  位置: app/services/
  特征: class.*Service, business logic
  命名: {domain}_service.py

```
## ❌ 禁止的错误位置
### 绝对不要创建的位置
```
错误位置列表:
  - app/services/          # 根目录app下
  - backend/app/services/  # 主后端服务下
  - tests/ai_service/      # 根目录tests下
  - tests/user_service/    # 根目录tests下
  - tests/course_service/  # 根目录tests下
  - tests/training_service/ # 根目录tests下

正确位置对应:
  - services/ai-service/app/services/
```
## 🔍 重复功能检测
### 检测规则
```
重复类检测:
  模式: class.*Service
  检查: 相同类名在多个文件中定义

重复函数检测:
  模式: def.*service, async def.*service
  检查: 相似功能的函数重复实现

重复API检测:
  模式: @router.post, @router.get
```
### 避免重复的策略
```
创建前检查:
  1. 搜索项目中是否已有类似功能
  2. 检查相同类名或函数名
  3. 验证API路径是否冲突
  4. 确认业务逻辑是否重复

重构建议:
  1. 合并相似功能的类
  2. 提取公共逻辑到基类
  3. 使用继承减少代码重复
```
## 🛠️ 自动化验证工具
### 1. Hook验证器
```
文件: .kiro/hooks/directory-structure-validator.kiro.hook
功能:
  - 实时检测文件创建位置
  - 验证服务边界
  - 检查重复功能
  - 提供修正建议
```
### 2. 结构验证脚本
```
文件: scripts/validate_project_structure.py
功能:
  - 全面检查项目结构
  - 生成详细验证报告
  - 提供自动修复建议
  - 定期结构健康检查
```
### 3. 简化检查脚本
```
文件: scripts/check_structure.py
功能:
  - 快速结构验证
  - 实时问题检测
  - 简洁的报告输出
  - CI/CD集成支持
```
## 📋 智能体编码工作流
### 标准工作流程
```
graph TD
    A[需要创建文件] --> B[确定业务领域]
    B --> C[选择目标微服务]
    C --> D[确定文件类型]
    D --> E[检查目录结构]
    E --> F[搜索重复功能]
    F --> G{发现重复?}
    G -->|是| H[重构或合并]
    G -->|否| I[创建文件]
    H --> I
```
### 检查命令
```
# 快速结构检查
python3 scripts/check_structure.py

# 详细验证报告
python3 scripts/validate_project_structure.py

# 查看验证报告
cat project_structure_report.json
```

## 📋 来源: directory-structure-guidelines.md

# 目录结构指导原则
## 🎯 核心原则
### 1. 单体架构模块化设计
### 2. 模块边界清晰
每个模块负责特定的业务领域，文件必须放在对应模块的目录下。
## 📁 标准目录结构
### 单体架构根目录结构
```
/
├── frontend/                    # 前端应用（React + TypeScript）
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   ├── pages/              # 页面组件
│   │   ├── hooks/              # 自定义Hooks
│   │   ├── stores/             # Zustand状态管理
│   │   ├── api/                # API调用
│   │   └── utils/              # 工具函数
│   ├── public/                 # 静态资源
```
### 模块标准结构
```
app/{module-name}/
├── __init__.py
├── api/                        # API路由
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── {domain}_endpoints.py
├── models/                     # 数据模型
│   ├── __init__.py
│   └── {domain}_models.py
```
## 🚨 单体架构模块文件放置规则
### 应用核心文件规则
```
应用核心文件位置规则:
  - 应用入口: app/main.py
  - 应用配置: app/core/config.py
  - 数据库配置: app/core/database.py
  - 依赖注入: app/core/deps.py
  - 共享工具: app/shared/

严重错误位置:
  ❌ backend/app/          # 不存在backend目录
  ❌ services/             # 不存在services目录
```
### AI模块相关文件
```
AI模块文件位置规则:
  - AI核心服务: app/ai/services/
  - AI API端点: app/ai/api/v1/
  - AI数据模型: app/ai/models/
  - AI请求响应模式: app/ai/schemas/
  - AI模块测试: tests/unit/ai/ 或 tests/integration/ai/
  - AI工具函数: app/ai/utils/

严重错误位置:
  ❌ services/ai-service/          # 微服务目录不存在
```
### 用户模块相关文件
```
用户模块文件位置规则:
  - 用户核心服务: app/users/services/
  - 用户API端点: app/users/api/v1/
  - 用户数据模型: app/users/models/
  - 用户模块测试: tests/unit/users/
```
### 课程模块相关文件
```
课程模块文件位置规则:
  - 课程核心服务: app/courses/services/
  - 课程API端点: app/courses/api/v1/
  - 课程数据模型: app/courses/models/
  - 课程模块测试: tests/unit/courses/
```
### 训练模块相关文件
```
训练模块文件位置规则:
  - 训练核心服务: app/training/services/
  - 训练API端点: app/training/api/v1/
  - 训练数据模型: app/training/models/
  - 训练模块测试: tests/unit/training/
```
## 🔍 智能体编码检查清单
### 创建文件前必须检查
### 文件创建决策树
```
graph TD
    A[需要创建文件] --> B{确定业务领域}
    B -->|AI相关| C[app/ai/]
    B -->|用户相关| D[app/users/]
    B -->|课程相关| E[app/courses/]
    B -->|训练相关| F[app/training/]
    B -->|通知相关| G[app/notifications/]
    B -->|分析相关| H[app/analytics/]
    B -->|资源相关| I[app/resources/]
    B -->|前端相关| J[frontend/]
```
## 📋 常见错误和修正
### 错误模式1：模块混乱
```
错误:
  - app/services/ai_service.py          # 应该在具体模块下
  - app/models/user_model.py            # 应该在具体模块下
  - tests/ai_service/test_ai.py         # 应该在tests/unit/ai/下

修正:
  - app/ai/services/ai_service.py
  - app/users/models/user_model.py
  - tests/unit/ai/test_ai.py
```
### 错误模式2：模块边界不清
```
错误:
  - app/ai/services/user_service.py     # 用户服务放在AI模块下
  - app/users/services/ai_service.py    # AI服务放在用户模块下

修正:
  - app/users/services/user_service.py
  - app/ai/services/ai_service.py
```
### 错误模式3：测试文件位置错误
```
错误:
  - tests/ai_service/test_temperature.py    # 应该按模块组织
  - app/ai/tests/test_ai_service.py         # 测试不应该在模块内

修正:
  - tests/unit/ai/test_temperature.py      # 单元测试按模块组织
  - tests/integration/ai/test_ai_integration.py  # 集成测试按模块组织
```
## 🛠️ 智能体实施指南
### 1. 文件创建前置检查函数
```
def validate_file_path(file_path: str, content_type: str) -> bool:
    """
    验证文件路径是否符合微服务架构规范

    Args:
        file_path: 要创建的文件路径
        content_type: 文件内容类型 (ai, user, course, training, notification)

    Returns:
        bool: 路径是否正确
```
### 2. 自动模块检测
```
def detect_module_from_content(content: str) -> str:
    """
    从文件内容检测应该属于哪个模块

    Args:
        content: 文件内容

    Returns:
        str: 模块名称
    """
```
