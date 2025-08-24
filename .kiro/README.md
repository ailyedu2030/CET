# Kiro 配置说明

## Agent Hooks 配置

Agent Hooks 是强大的自动化工具，通过在特定事件发生时执行预定义的agent动作来简化开发工作流程。

### 🎯 什么是Agent Hooks？

Agent Hooks是自动化触发器，当IDE中发生特定事件时执行预定义的agent动作。它们通过智能自动化转变您的开发工作流程：

- 保持一致的代码质量
- 防止安全漏洞
- 减少手动开销
- 标准化团队流程
- 创建更快的开发周期

### 📁 已配置的Agent Hooks

#### 1. 代码质量Agent (code-quality-agent.json)
- **触发条件**: 保存 TypeScript/Python/JavaScript 文件时自动运行
- **功能**: 
  - 自动检查类型安全和ESLint违规
  - 检查Python类型提示和PEP 8合规性
  - 识别潜在的bug和安全问题
  - 自动修复发现的问题
- **自动执行**: 是

#### 2. 文档助手 (documentation-helper.json)
- **触发条件**: 保存Markdown文件时
- **功能**:
  - 检查语法和拼写错误
  - 改善清晰度和可读性
  - 确保正确的Markdown格式
  - 更新目录（如果存在）
- **自动执行**: 否（需要手动确认）

#### 3. 测试生成器 (test-generator.json)
- **触发条件**: 创建新的代码文件时
- **功能**:
  - 分析代码结构和函数
  - 生成全面的单元测试
  - 包含边界情况和错误场景
  - 遵循语言的测试最佳实践
- **自动执行**: 否（需要手动确认）

#### 4. 安全扫描器 (security-scanner.json)
- **触发条件**: 保存代码文件时
- **功能**:
  - 扫描常见安全问题（SQL注入、XSS等）
  - 查找硬编码的密钥或凭据
  - 识别不安全的依赖或导入
  - 检查输入验证和认证逻辑
- **自动执行**: 否（需要手动确认）

#### 5. 项目分析器 (project-analyzer.json)
- **触发条件**: 手动触发
- **功能**:
  - 分析整体架构和组织
  - 识别重构机会
  - 检查缺失的文档或配置
  - 建议技术栈最佳实践
- **自动执行**: 否

#### 6. 快速测试 (quick-test.json)
- **触发条件**: 保存测试文件时或手动触发
- **功能**:
  - 验证项目结构
  - 检查关键依赖
  - 运行现有测试
  - 提供项目健康摘要
- **自动执行**: 否

#### 7. 网络研究助手 (web-research-assistant.json)
- **触发条件**: 手动触发
- **功能**:
  - 浏览相关网站收集信息
  - 提取网页关键内容
  - 截图重要内容
  - 结构化总结研究结果
- **自动执行**: 否
- **特殊功能**: 使用Chrome MCP服务器进行网页浏览

#### 8. 文档验证器 (documentation-validator.json)
- **触发条件**: 保存Markdown文件时
- **功能**:
  - 对照官方文档验证事实
  - 验证代码示例和语法
  - 检查链接有效性
  - 识别过时信息
- **自动执行**: 否
- **特殊功能**: 使用Chrome MCP服务器验证在线资源

## MCP 服务器配置

MCP 服务器已配置在 `.kiro/settings/mcp.json` 中，包含以下工具：

### 1. Chrome MCP 服务器 (chrome-mcp-server)
- **功能**: 浏览器自动化和网页交互
- **自动批准操作**: 导航、截图、获取页面内容、点击、输入
- **状态**: 已启用
- **连接**: HTTP流式连接到 http://127.0.0.1:12306/mcp
- **用途**: 网页浏览、数据抓取、UI测试、网页内容分析

### 2. Brave 搜索服务器 (brave-search)
- **功能**: 网络搜索
- **状态**: 已禁用（需要 API 密钥）
- **启用方法**: 设置环境变量 `BRAVE_API_KEY` 并将 `disabled` 改为 `false`

## 使用建议

### 开发流程
1. **项目开始**: 运行 "项目初始化设置" Hook
2. **环境检查**: 运行 "开发环境检查" Hook
3. **日常开发**: 代码质量检查会自动运行
4. **测试验证**: 使用 "快速测试" Hook 进行快速验证
5. **任务完成**: 运行 "任务完成验证" Hook 进行全面检查

### 故障排除

#### MCP 服务器连接失败
1. 确保已安装 Node.js 和 npm
2. 检查网络连接
3. 尝试手动运行 MCP 服务器命令：
   ```bash
   npx -y @modelcontextprotocol/server-filesystem /Users
   ```

#### Hooks 执行失败
1. 检查项目目录结构是否正确
2. 确保已安装相关依赖（Node.js、Python、npm、pip）
3. 检查环境变量配置
4. 查看 Kiro 日志获取详细错误信息

### 自定义配置

#### 添加新的 Hook
1. 在 `.kiro/hooks/` 目录下创建新的 JSON 文件
2. 参考现有 Hook 的格式
3. 重启 Kiro 以加载新配置

#### 修改 MCP 服务器
1. 编辑 `.kiro/settings/mcp.json` 文件
2. 添加或修改服务器配置
3. 重启 Kiro 或在 MCP 面板中重新连接

## 环境变量

创建 `.env` 文件并设置以下变量（可选）：

```bash
# Brave 搜索 API（可选）
BRAVE_API_KEY=your_brave_api_key

# 数据库连接（如果使用 PostgreSQL）
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# AI 服务 API 密钥（项目需要时）
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
```

## 支持

如果遇到问题：
1. 检查 Kiro 日志
2. 确认环境配置
3. 参考本文档的故障排除部分
4. 查看具体的错误信息进行针对性解决
### 🚀
 如何使用Agent Hooks

#### 方法1: 通过Explorer View
1. 在Kiro面板中导航到"Agent Hooks"部分
2. 点击 + 按钮创建新hook
3. 使用自然语言定义hook工作流程
4. 按Enter或点击Submit继续
5. 配置hook设置并保存

#### 方法2: 通过命令面板
1. 打开命令面板：`Cmd + Shift + P` (Mac) 或 `Ctrl + Shift + P` (Windows/Linux)
2. 输入 "Kiro: Open Kiro Hook UI"
3. 按照屏幕指示创建您的hook

#### 方法3: 手动触发现有Hooks
1. 在Agent Hooks面板中找到要执行的hook
2. 点击hook名称旁的运行按钮
3. 或通过命令面板搜索hook名称

### ⚙️ Hook配置格式

每个Agent Hook包含以下关键元素：

```json
{
  "name": "Hook名称",
  "description": "Hook描述",
  "triggers": [
    {
      "type": "file_save|file_create|manual",
      "patterns": ["*.ts", "*.py"]  // 可选：文件模式
    }
  ],
  "prompt": "发送给agent的详细提示...",
  "autoExecute": true|false,  // 是否自动执行
  "settings": {
    "timeout": 60,
    "retryCount": 1
  }
}
```

### 🔧 故障排除

#### Hook没有显示在界面中
1. 重启Kiro IDE
2. 重新打开工作区：File → Close Workspace → File → Open Workspace
3. 检查JSON配置文件格式是否正确
4. 确保文件权限正确（644）

#### Hook无法执行
1. 检查Kiro的输出面板获取错误信息
2. 确保prompt内容清晰明确
3. 验证触发条件是否正确设置
4. 检查autoExecute设置是否符合预期

#### 自动触发不工作
1. 确认文件模式匹配正确
2. 检查autoExecute设置
3. 验证触发类型（file_save, file_create, manual）
4. 重启Kiro以重新加载配置

### 📚 最佳实践

1. **明确的提示**: 为agent提供清晰、具体的指令
2. **适当的自动化**: 只对安全的操作启用autoExecute
3. **合理的超时**: 根据任务复杂度设置适当的超时时间
4. **测试先行**: 先手动测试hook，确认工作正常后再启用自动执行
5. **渐进式部署**: 从简单的hook开始，逐步增加复杂性

### 🎯 下一步

现在您已经配置了Agent Hooks，可以：

1. **重启Kiro IDE**以加载新配置
2. **测试手动触发**：尝试运行"项目分析器"hook
3. **测试自动触发**：保存一个TypeScript或Python文件，观察代码质量agent是否自动运行
4. **自定义hooks**：根据您的项目需求创建更多专用hooks
5. **查看官方文档**：访问 https://kiro.dev/docs/hooks/ 了解更多高级功能

通过这些Agent Hooks，您的开发工作流程将变得更加智能和高效！