# Cursor 规则快速参考

## 🚀 快捷命令

在 Cursor Chat 中使用以下命令获取详细规则：

### 文档快捷方式
- `@docs` - project context
- `@ai-rules` - deepseek optimization guide
- `@edu-rules` - education system standards
- `@perf-rules` - realtime response strategy
- `@code-rules` - intelligent agent coding guidelines
- `@task-rules` - task execution standards
- `@temp-rules` - deepseek temperature config

### 使用示例

#### 检查文件位置
```
根据 @code-rules，这个用户认证文件应该放在哪个目录？
```

#### AI服务集成检查
```
读取 .cursor/rules-ai.md 并检查这个DeepSeek API调用是否符合规范
```

#### 教育系统合规检查
```
参考 @edu-rules 验证这个学生数据处理逻辑的合规性
```

#### 性能优化分析
```
根据 @perf-rules 分析这段代码的性能问题
```

## 📋 核心检查清单

### 文件创建前
- [ ] 确定业务领域
- [ ] 选择目标模块 (app/users/, app/ai/, app/courses/ 等)
- [ ] 确认文件类型 (API/服务/模型/测试)

### 代码编写时
- [ ] 遵循TypeScript/Python编码规范
- [ ] 实现完整的错误处理
- [ ] 添加适当的输入验证
- [ ] 考虑性能和安全要求

### 提交前检查
- [ ] 运行代码质量检查
- [ ] 验证模块边界
- [ ] 检查教育系统合规性
- [ ] 确认AI服务调用规范

## 🔧 工具命令

```bash
# 更新规则文件
node scripts/cursor-docs-helper.js --update

# 生成Chat提示
node scripts/cursor-docs-helper.js --prompt @ai-rules

# 检查规则文件状态
node scripts/cursor-docs-helper.js --status
```
