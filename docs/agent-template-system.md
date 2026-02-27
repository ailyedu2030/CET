# 智能体自动模板调用系统

## 🎯 系统目标

确保每个智能体在执行任务时都会**自动调用模板**，无需手动干预，实现：
- ✅ **强制模板使用** - 所有工具调用都通过模板系统
- ✅ **标准化流程** - 统一的5阶段执行标准
- ✅ **质量保证** - 内置检查清单和验收标准
- ✅ **自动拦截** - 运行时自动拦截所有工具调用

## 🏗️ 系统架构

### 核心组件

1. **智能体包装器** (`scripts/agent-wrapper.py`)
   - 自动拦截所有工具调用
   - 强制应用模板检查清单
   - 记录执行日志和验证结果

2. **智能体注册中心** (`scripts/agent-registry.py`)
   - 自动注册所有智能体
   - 为每个智能体包装工具函数
   - 管理智能体角色和权限

3. **系统启动器** (`scripts/start-agent-system.py`)
   - 自动初始化整个系统
   - 设置环境变量和拦截器
   - 提供统一的执行入口

4. **模板管理器** (`scripts/agent-templates.py`)
   - 定义标准化的5阶段模板
   - 管理检查清单和成功标准
   - 支持灵活的模板配置

## 🔧 自动调用机制

### 1. 环境变量触发
```bash
export AGENT_SYSTEM_ENABLED=true
export AUTO_TEMPLATE_ENABLED=true
```

### 2. 工具拦截器
```python
# 自动拦截所有Augment工具调用
tool_interceptor.intercept_all_tools()

# 包装后的工具会自动应用模板
@template_wrapper("view")
def wrapped_view(*args, **kwargs):
    # 自动执行模板检查
    return original_view(*args, **kwargs)
```

### 3. 智能体注册
```python
# 智能体注册时自动包装所有工具
agent_registry.register_agent("coordinator", AgentRole.COORDINATOR)
# 所有工具调用都会自动使用模板
```

### 4. 上下文管理
```python
# 设置执行上下文后，所有工具调用都会自动应用模板
template_enforcer.start_requirement_execution("23", TaskPhase.PHASE_1)
```

## 🚀 使用方法

### 方法1：直接启动系统
```bash
# 启动智能体系统（自动启用模板）
python scripts/start-agent-system.py init

# 执行需求（自动使用模板）
python scripts/start-agent-system.py execute 23
```

### 方法2：在代码中自动启用
```python
# 导入模块时自动检查环境变量
import agent_wrapper  # 自动启用模板系统

# 或者手动启动
from agent_registry import init_agent_system
init_agent_system()  # 自动注册并包装所有智能体
```

### 方法3：装饰器方式
```python
from agent_wrapper import auto_template_call

@auto_template_call("23", TaskPhase.PHASE_1)
def execute_requirement_23():
    # 这个函数内的所有工具调用都会自动使用模板
    view(".kiro/specs/cet4-learning-system/requirements.md")
    codebase_retrieval("需求23相关代码")
```

## 🛡️ 强制执行保证

### 1. 运行时拦截
- 系统启动时自动拦截所有工具函数
- 无法绕过模板系统直接调用工具
- 所有调用都会经过模板验证

### 2. 环境检查
```python
def ensure_template_usage():
    """确保模板使用的全局函数"""
    if not template_enforcer.agent_context.auto_template_enabled:
        print("⚠️ 自动启用模板系统")
        template_enforcer.enable_auto_template()
```

### 3. 智能体包装
```python
# 每个智能体的工具都被自动包装
wrapped_tools = {
    'view': template_wrapper('view')(original_view),
    'codebase-retrieval': template_wrapper('codebase-retrieval')(original_retrieval),
    # ... 所有工具都被包装
}
```

### 4. 配置强制
```json
{
  "system": {
    "auto_template_enabled": true,
    "force_template_usage": true,
    "allow_bypass": false
  }
}
```

## 📋 模板执行流程

### 自动执行的5个阶段

1. **阶段1：强制检查清单执行**
   ```
   ✅ 需求文档一致性检查
   ✅ 设计文档冲突检查  
   ✅ 用户确认检查
   ✅ 文档依据检查
   ✅ 不确定性报告
   ```

2. **阶段2：需求深度分析**
   ```
   ✅ 功能要求解读
   ✅ 技术要求明确
   ✅ 验收标准提取
   ✅ 依赖关系识别
   ✅ 实现范围确定
   ```

3. **阶段3：现状全面评估**
   ```
   ✅ 前端实现状态检查
   ✅ 后端实现状态检查
   ✅ 数据库状态检查
   ✅ 集成状态检查
   ✅ 测试覆盖检查
   ```

4. **阶段4：实现方案制定**
   ```
   ✅ 技术栈选择
   ✅ 架构一致性确保
   ✅ 代码复用规划
   ✅ 渐进式实现设计
   ```

5. **阶段5：代码实现与验证**
   ```
   ✅ 前端代码补全
   ✅ 后端代码补全
   ✅ 质量标准保证
   ✅ 功能验证
   ✅ 集成测试
   ```

## 🔍 验证机制

### 执行前检查
```python
def _pre_execution_check(tool_name: str, template, *args, **kwargs):
    """每次工具调用前自动执行"""
    print(f"📋 执行前检查 - {tool_name}")
    # 显示检查清单
    # 验证参数合理性
    # 确认模板要求
```

### 执行后验证
```python
def _post_execution_validation(tool_name: str, template, result):
    """每次工具调用后自动执行"""
    print(f"✅ 执行后验证 - {tool_name}")
    # 检查成功标准
    # 验证结果质量
    # 记录执行日志
```

### 质量门控
```python
quality_gates = [
    "文档完整性检查通过",
    "用户确认获得", 
    "技术可行性验证",
    "代码质量检查通过",
    "功能测试通过"
]
```

## 📊 监控和报告

### 自动生成报告
```python
def _generate_phase_report(self):
    """自动生成阶段执行报告"""
    print(f"📊 阶段执行报告:")
    print(f"  工具调用次数: {total_count}")
    print(f"  成功次数: {success_count}")
    print(f"  成功率: {success_count/total_count*100:.1f}%")
```

### 执行日志
```json
{
  "tool_name": "view",
  "requirement_id": "23",
  "phase": "阶段1：强制检查清单执行",
  "template_used": true,
  "status": "success",
  "checklist_items": [...],
  "success_criteria": [...]
}
```

## 🎯 关键优势

1. **零遗漏保证** - 无法绕过模板系统
2. **自动化执行** - 无需手动干预
3. **标准化流程** - 所有智能体使用相同标准
4. **质量保证** - 内置检查和验证机制
5. **完整追踪** - 详细的执行日志和报告

## 🔧 故障排除

### 模板未启用
```bash
# 检查环境变量
echo $AGENT_SYSTEM_ENABLED
echo $AUTO_TEMPLATE_ENABLED

# 手动启用
python scripts/start-agent-system.py init
```

### 工具调用绕过模板
```python
# 检查拦截器状态
if not tool_interceptor.intercepted:
    tool_interceptor.intercept_all_tools()

# 检查智能体注册
agent_registry.list_registered_agents()
```

### 模板执行失败
```python
# 查看执行日志
template_enforcer.generate_execution_report()

# 检查模板配置
template_manager.get_phase_template(TaskPhase.PHASE_1)
```

通过这套系统，**确保每个智能体都会自动调用模板**，实现标准化、高质量的任务执行。
