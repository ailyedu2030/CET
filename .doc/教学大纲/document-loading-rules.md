# 教学大纲系统文档按需加载规则

## 📋 文档分类和加载策略

### 核心原则

- **按需加载** - 只在特定开发阶段加载相关文档
- **分层管理** - 区分核心文档、参考文档和详细文档
- **智能调取** - 根据当前任务自动推荐相关文档

## 📚 文档分类体系

### 1. 核心规则文档 (始终加载)

```yaml
core_documents:
  - development-rules-and-constraints.md      # 开发规则和约束
  - ai-agent-deviation-prevention.md          # AI开发偏差防控
  priority: ALWAYS_LOAD
  size: MEDIUM
  usage: 所有开发阶段
```

### 2. 阶段性技术文档 (按阶段加载)

```yaml
phase_documents:
  第一阶段_基础优化:
    - deepseek-optimization-strategy.md       # DeepSeek优化策略
    - teaching-syllabus-architecture-improvement.md  # 架构改进
    priority: HIGH
    trigger: 开始第一阶段任务时加载

  第二阶段_智能分析:
    - comprehensive-teaching-system-optimization.md  # 全面优化方案
    - teaching-syllabus-technical-implementation.md  # 技术实现
    priority: HIGH
    trigger: 开始第二阶段任务时加载

  第三阶段_个性化生成:
    - comprehensive-teaching-system-optimization.md  # 全面优化方案
    priority: MEDIUM
    trigger: 开始第三阶段任务时加载

  第四阶段_协作优化:
    - comprehensive-teaching-system-roadmap.md       # 实施路线图
    priority: MEDIUM
    trigger: 开始第四阶段任务时加载

  第五阶段_高级功能:
    - comprehensive-teaching-system-roadmap.md       # 实施路线图
    priority: LOW
    trigger: 开始第五阶段任务时加载

  第六阶段_部署上线:
    - project-implementation-guide.md                # 实施指南
    - comprehensive-teaching-system-roadmap.md       # 实施路线图
    priority: HIGH
    trigger: 开始第六阶段任务时加载
```

### 3. 参考文档 (按需调取)

```yaml
reference_documents:
  - teaching-syllabus-system-analysis.md      # 系统现状分析
  - teaching-syllabus-data-models.md          # 数据模型设计
  - teaching-syllabus-api-design.md           # API设计规范
  - deepseek-implementation-examples.md       # DeepSeek实现示例
  - deepseek-optimizer-code-generation-examples.md  # 代码生成示例
  priority: ON_DEMAND
  trigger: 特定任务需要时手动加载
```

### 4. 总结文档 (项目管理时加载)

```yaml
summary_documents:
  - task-list-summary.md                      # 任务清单总结
  - final-task-review-report.md               # 最终审查报告
  priority: MANAGEMENT
  trigger: 项目管理和进度跟踪时加载
```

## 🎯 按任务类型的文档加载规则

### DeepSeek相关任务

```yaml
deepseek_tasks:
  required_docs:
    - development-rules-and-constraints.md
    - deepseek-optimization-strategy.md
  optional_docs:
    - deepseek-implementation-examples.md
  load_trigger: 任务名称包含"DeepSeek"或"模型"
```

### 前端UI/UX任务

```yaml
frontend_tasks:
  required_docs:
    - development-rules-and-constraints.md
    - comprehensive-teaching-system-optimization.md
  optional_docs:
    - teaching-syllabus-api-design.md
  load_trigger: 任务名称包含"UI"、"界面"或"前端"
```

### 后端API任务

```yaml
backend_tasks:
  required_docs:
    - development-rules-and-constraints.md
    - teaching-syllabus-architecture-improvement.md
  optional_docs:
    - teaching-syllabus-api-design.md
    - teaching-syllabus-data-models.md
  load_trigger: 任务名称包含"API"、"后端"或"数据库"
```

### 测试和部署任务

```yaml
deployment_tasks:
  required_docs:
    - development-rules-and-constraints.md
    - project-implementation-guide.md
  optional_docs:
    - comprehensive-teaching-system-roadmap.md
  load_trigger: 任务名称包含"测试"、"部署"或"上线"
```

## 🔄 智能加载机制

### 自动加载规则

```python
def get_required_documents(current_task, current_phase):
    """根据当前任务和阶段自动确定需要加载的文档"""

    # 始终加载核心规则文档
    required_docs = [
        "development-rules-and-constraints.md",
        "ai-agent-deviation-prevention.md"
    ]

    # 根据阶段加载对应文档
    phase_docs = {
        "第一阶段": ["deepseek-optimization-strategy.md",
                   "teaching-syllabus-architecture-improvement.md"],
        "第二阶段": ["comprehensive-teaching-system-optimization.md",
                   "teaching-syllabus-technical-implementation.md"],
        "第三阶段": ["comprehensive-teaching-system-optimization.md"],
        "第四阶段": ["comprehensive-teaching-system-roadmap.md"],
        "第五阶段": ["comprehensive-teaching-system-roadmap.md"],
        "第六阶段": ["project-implementation-guide.md",
                   "comprehensive-teaching-system-roadmap.md"]
    }

    if current_phase in phase_docs:
        required_docs.extend(phase_docs[current_phase])

    # 根据任务类型加载特定文档
    task_keywords = {
        "DeepSeek": ["deepseek-optimization-strategy.md"],
        "UI": ["comprehensive-teaching-system-optimization.md"],
        "API": ["teaching-syllabus-api-design.md"],
        "数据库": ["teaching-syllabus-data-models.md"],
        "测试": ["project-implementation-guide.md"],
        "部署": ["project-implementation-guide.md"]
    }

    for keyword, docs in task_keywords.items():
        if keyword in current_task:
            required_docs.extend(docs)

    # 去重并返回
    return list(set(required_docs))
```

### 手动调取规则

```python
def request_additional_document(document_name, reason):
    """手动请求加载额外文档"""

    available_docs = {
        "系统分析": "teaching-syllabus-system-analysis.md",
        "数据模型": "teaching-syllabus-data-models.md",
        "API设计": "teaching-syllabus-api-design.md",
        "代码示例": "deepseek-implementation-examples.md",
        "实施指南": "project-implementation-guide.md"
    }

    if document_name in available_docs:
        return f"加载文档: {available_docs[document_name]}"
    else:
        return "文档不存在或不可用"
```

## 📊 文档大小和优先级管理

### 文档大小分类

```yaml
document_sizes:
  SMALL: # < 50KB
    - development-rules-and-constraints.md
    - ai-agent-deviation-prevention.md

  MEDIUM: # 50KB - 200KB
    - deepseek-optimization-strategy.md
    - teaching-syllabus-architecture-improvement.md
    - project-implementation-guide.md

  LARGE: # > 200KB
    - comprehensive-teaching-system-optimization.md
    - teaching-syllabus-technical-implementation.md
    - comprehensive-teaching-system-roadmap.md
```

### 加载优先级

```yaml
loading_priority:
  CRITICAL: # 必须加载，影响开发质量
    - development-rules-and-constraints.md
    - ai-agent-deviation-prevention.md

  HIGH: # 当前阶段重要文档
    - 根据阶段动态确定

  MEDIUM: # 参考文档，按需加载
    - teaching-syllabus-api-design.md
    - teaching-syllabus-data-models.md

  LOW: # 背景信息，可选加载
    - teaching-syllabus-system-analysis.md
    - task-list-summary.md
```

## 🎯 使用建议

### 开发团队使用指南

1. **项目启动时** - 只加载核心规则文档
2. **开始新阶段** - 自动加载对应阶段文档
3. **遇到具体问题** - 手动调取相关参考文档
4. **项目管理时** - 加载总结和进度文档

### AI助手使用规则

1. **默认加载** - 仅加载核心规则文档
2. **任务驱动** - 根据当前任务自动推荐文档
3. **按需响应** - 用户请求时加载特定文档
4. **智能提醒** - 提示可能需要的相关文档

### 文档维护规则

1. **定期清理** - 移除过时或重复的文档
2. **大小控制** - 单个文档不超过300KB
3. **内容精简** - 保留核心信息，详细内容分离
4. **索引更新** - 及时更新文档分类和加载规则

---

**规则版本**: v1.0  
**创建日期**: 2025-01-22  
**适用范围**: 教学大纲系统开发项目  
**更新频率**: 根据项目进展动态调整
