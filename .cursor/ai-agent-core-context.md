# Cursor 智能体开发核心上下文

## 🤖 智能体必读：项目本质理解

### 🎯 项目核心

你正在开发一个**英语四级学习系统**，这是一个 AI 驱动的教育平台：

- **核心价值**：通过 AI 智能批改和个性化训练，提升学生四级考试成绩
- **技术特点**：单体架构 + DeepSeek AI + 实时批改 + 智能分析
- **用户角色**：管理员(系统管理) + 教师(教学管理) + 学生(学习训练)

### 🏗️ 架构约束 (智能体必须遵守)

1. **模块边界严格**：绝对禁止跨模块混合业务逻辑
2. **文件放置规则**：
   - 用户相关 → `app/users/`
   - AI 相关 → `app/ai/`
   - 训练相关 → `app/training/`
   - 课程相关 → `app/courses/`
   - 通知相关 → `app/notifications/`
   - 分析相关 → `app/analytics/`
   - 资源相关 → `app/resources/`
3. **代码质量零容忍**：每个文件创建后必须通过 Ruff + mypy + ESLint 检查

### 🎓 教育业务核心逻辑 (智能体必须理解)

1. **智能训练闭环**：
   ```
   学生训练 → AI分析 → 教师调整 → 内容优化 → 学生训练
   ```
2. **AI 批改标准**：严格按英语四级评分标准，准确率>90%
3. **个性化学习**：基于学生薄弱点生成针对性训练内容
4. **数据安全**：学生数据加密存储，未成年人保护机制

### 🔧 开发模式 (智能体必须执行)

- **一次成型开发**：每个功能必须一次性完整实现
- **零返工原则**：设计和实现必须准确无误
- **完整测试**：单元测试>80%，集成测试>70%

## 🚨 智能体开发检查清单

在编写任何代码前，智能体必须确认：

1. [ ] 明确这个文件属于哪个业务模块？
2. [ ] 是否违反了模块边界约束？
3. [ ] 是否符合教育系统的业务逻辑？
4. [ ] 是否包含完整的错误处理？
5. [ ] 是否符合 AI 服务调用规范？

## 💡 智能体提示词模板

当智能体需要实现功能时，使用以下提示词：

```
"基于英语四级学习系统的完整规范，实现[具体功能]。
请确保：
1. 遵循模块化架构约束
2. 符合教育业务逻辑
3. 包含完整的AI服务集成
4. 通过所有代码质量检查
5. 提供完整的测试用例

参考文档：[相关规则文件]"
```

## 🎯 核心模块开发指南

### app/training/ - 系统核心模块

- **职责**：五大训练类型(词汇/听力/阅读/写作/翻译)
- **关键逻辑**：智能批改、自适应难度、错题分析
- **AI 集成**：DeepSeek 生成题目和批改

### app/ai/ - AI 服务引擎

- **职责**：DeepSeek API 集成、智能分析、内容生成
- **关键要求**：流式输出、降级策略、成本控制
- **性能要求**：批改<3s，题目生成<2s

### app/users/ - 用户管理

- **职责**：认证授权、权限控制、用户信息管理
- **安全要求**：JWT 认证、RBAC 权限、数据加密
- **教育合规**：未成年人保护、数据脱敏

## 🔍 智能体快速参考

### 常用规则文件引用

- AI 服务规范：`.cursor/rules-ai.md`
- 教育系统要求：`.cursor/rules-education.md`
- 性能优化：`.cursor/rules-performance.md`
- 安全防护：`.cursor/rules-security.md`

### 代码生成标准

```python
# Python代码必须包含
from typing import Optional, List, Dict, Any
import asyncio
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 所有函数必须有类型注解
async def function_name(param: str) -> Dict[str, Any]:
    try:
        # 业务逻辑
        result = await some_operation(param)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error in function_name: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

```typescript
// TypeScript代码必须包含
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

// 所有函数必须有明确返回类型
const functionName = async (param: string): Promise<ApiResponse<DataType>> => {
  try {
    const result = await apiCall(param)
    return { success: true, data: result }
  } catch (error) {
    console.error('Error in functionName:', error)
    return { success: false, error: 'Operation failed' }
  }
}
```
