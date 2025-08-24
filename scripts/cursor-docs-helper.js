#!/usr/bin/env node

/**
 * Cursor 文档助手脚本
 * 从 .kiro/steering 目录提取核心规则，生成 Cursor 可用的精简规则文件
 */

const fs = require('fs');
const path = require('path');

class CursorDocsHelper {
  constructor() {
    this.projectRoot = process.cwd();
    this.steeringPath = path.join(this.projectRoot, '.kiro/steering');
    this.cursorPath = path.join(this.projectRoot, '.cursor');

    // 确保 .cursor 目录存在
    if (!fs.existsSync(this.cursorPath)) {
      fs.mkdirSync(this.cursorPath, { recursive: true });
    }

    // 文档快捷方式映射
    this.shortcuts = {
      '@docs': 'project-context.md',
      '@ai-rules': 'deepseek-optimization-guide.md',
      '@edu-rules': 'education-system-standards.md',
      '@perf-rules': 'realtime-response-strategy.md',
      '@code-rules': 'intelligent-agent-coding-guidelines.md',
      '@task-rules': 'task-execution-standards.md',
      '@temp-rules': 'deepseek-temperature-config.md'
    };

    // 核心规则提取配置
    this.extractionRules = {
      'rules-core.md': {
        sources: ['intelligent-agent-coding-guidelines.md', 'directory-structure-guidelines.md'],
        patterns: [
          /^#{1,3}\s+/,           // 标题
          /^\s*-\s+/,             // 列表项
          /必须|禁止|严重错误|强制/,    // 强制性规则
          /^```/,                 // 代码块开始
          /^app\//,               // 目录结构
          /关键词:/               // 关键词匹配
        ],
        maxLines: 150
      },
      'rules-ai-extended.md': {
        sources: ['deepseek-optimization-guide.md', 'ai-service-temperature-update.md'],
        patterns: [
          /DeepSeek|AI服务|温度参数|密钥池/,
          /^#{1,3}\s+/,
          /^\s*-\s+/,
          /错峰|缓存|成本|优化/,
          /流式|批改|实时/
        ],
        maxLines: 200
      },
      'rules-education-extended.md': {
        sources: ['education-system-standards.md'],
        patterns: [
          /教育|学生|未成年|数据保护|合规/,
          /^#{1,3}\s+/,
          /^\s*-\s+/,
          /GDPR|个人信息保护法|网络安全法/,
          /时长限制|深夜禁用/
        ],
        maxLines: 150
      },
      'rules-performance-extended.md': {
        sources: ['realtime-response-strategy.md', 'realtime-performance-testing.md'],
        patterns: [
          /性能|响应时间|并发|缓存/,
          /^#{1,3}\s+/,
          /^\s*-\s+/,
          /ms|秒|延迟|吞吐/,
          /Redis|数据库|索引/
        ],
        maxLines: 150
      }
    };
  }

  /**
   * 提取文档的核心要点
   */
  extractKeyPoints(content, patterns, maxLines = 100) {
    const lines = content.split('\n');
    const keyPoints = [];
    let inCodeBlock = false;
    let codeBlockContent = [];

    for (let i = 0; i < lines.length && keyPoints.length < maxLines; i++) {
      const line = lines[i];

      // 处理代码块
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          // 代码块结束
          if (codeBlockContent.length > 0) {
            keyPoints.push('```');
            keyPoints.push(...codeBlockContent.slice(0, 10)); // 限制代码块长度
            keyPoints.push('```');
          }
          codeBlockContent = [];
        }
        inCodeBlock = !inCodeBlock;
        continue;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        continue;
      }

      // 检查是否匹配提取模式
      const shouldExtract = patterns.some(pattern => {
        if (typeof pattern === 'string') {
          return line.includes(pattern);
        }
        return pattern.test(line);
      });

      if (shouldExtract) {
        keyPoints.push(line);
      }
    }

    return keyPoints;
  }

  /**
   * 生成扩展规则文件
   */
  generateExtendedRules() {
    console.log('🔄 正在生成扩展规则文件...');

    Object.entries(this.extractionRules).forEach(([outputFile, config]) => {
      let extractedContent = `# ${outputFile.replace('.md', '').replace('rules-', '').replace('-extended', '')} - 扩展规则\n\n`;
      extractedContent += `> 本文件从 .kiro/steering 目录自动提取生成\n`;
      extractedContent += `> 生成时间: ${new Date().toISOString()}\n\n`;

      config.sources.forEach(sourceFile => {
        const sourcePath = path.join(this.steeringPath, sourceFile);
        if (fs.existsSync(sourcePath)) {
          console.log(`  📄 处理文件: ${sourceFile}`);

          const content = fs.readFileSync(sourcePath, 'utf8');
          const keyPoints = this.extractKeyPoints(content, config.patterns, config.maxLines);

          extractedContent += `\n## 📋 来源: ${sourceFile}\n\n`;
          extractedContent += keyPoints.join('\n') + '\n';

          console.log(`    ✅ 提取了 ${keyPoints.length} 行关键内容`);
        } else {
          console.log(`    ⚠️  文件不存在: ${sourceFile}`);
        }
      });

      const outputPath = path.join(this.cursorPath, outputFile);
      fs.writeFileSync(outputPath, extractedContent);

      const fileSize = (fs.statSync(outputPath).size / 1024).toFixed(1);
      console.log(`  ✅ 生成 ${outputFile} (${fileSize}KB)`);
    });
  }

  /**
   * 获取特定文档的摘要
   */
  getDocSummary(shortcut) {
    const filename = this.shortcuts[shortcut];
    if (!filename) {
      console.log(`❌ 未知的快捷方式: ${shortcut}`);
      console.log(`可用的快捷方式: ${Object.keys(this.shortcuts).join(', ')}`);
      return null;
    }

    const fullPath = path.join(this.steeringPath, filename);
    if (!fs.existsSync(fullPath)) {
      console.log(`❌ 文件不存在: ${filename}`);
      return null;
    }

    const content = fs.readFileSync(fullPath, 'utf8');

    // 提取前50行重要内容
    const summaryPatterns = [
      /^#{1,3}\s+/,     // 标题
      /^\s*-\s+/,       // 列表
      /必须|禁止|要求/,   // 重要规则
      /^>/,             // 引用
      /\*\*.*\*\*/      // 加粗文本
    ];

    const summary = this.extractKeyPoints(content, summaryPatterns, 50);
    return summary.join('\n');
  }

  /**
   * 生成 Cursor Chat 提示模板
   */
  generateChatPrompt(shortcut, context = '') {
    const summary = this.getDocSummary(shortcut);
    if (!summary) return null;

    return `
请根据以下规则分析代码${context ? ` (${context})` : ''}：

${summary}

请重点检查：
1. 架构合规性 - 是否符合单体架构模块化设计
2. 模块边界 - 文件是否放在正确的模块目录
3. 业务逻辑 - 是否符合教育系统特殊要求
4. 性能和安全 - 是否满足性能和安全标准

请提供具体的问题描述和改进建议。
`.trim();
  }

  /**
   * 创建快速参考文件
   */
  createQuickReference() {
    const quickRef = `# Cursor 规则快速参考

## 🚀 快捷命令

在 Cursor Chat 中使用以下命令获取详细规则：

### 文档快捷方式
${Object.entries(this.shortcuts).map(([shortcut, file]) =>
  `- \`${shortcut}\` - ${file.replace('.md', '').replace(/-/g, ' ')}`
).join('\n')}

### 使用示例

#### 检查文件位置
\`\`\`
根据 @code-rules，这个用户认证文件应该放在哪个目录？
\`\`\`

#### AI服务集成检查
\`\`\`
读取 .cursor/rules-ai.md 并检查这个DeepSeek API调用是否符合规范
\`\`\`

#### 教育系统合规检查
\`\`\`
参考 @edu-rules 验证这个学生数据处理逻辑的合规性
\`\`\`

#### 性能优化分析
\`\`\`
根据 @perf-rules 分析这段代码的性能问题
\`\`\`

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

\`\`\`bash
# 更新规则文件
node scripts/cursor-docs-helper.js --update

# 生成Chat提示
node scripts/cursor-docs-helper.js --prompt @ai-rules

# 检查规则文件状态
node scripts/cursor-docs-helper.js --status
\`\`\`
`;

    fs.writeFileSync(path.join(this.cursorPath, 'quick-reference.md'), quickRef);
    console.log('📚 创建快速参考文件: .cursor/quick-reference.md');
  }

  /**
   * 检查规则文件状态
   */
  checkStatus() {
    console.log('📊 Cursor 规则文件状态检查\n');

    // 检查主规则文件
    const mainRulesPath = path.join(this.projectRoot, '.cursorrules');
    if (fs.existsSync(mainRulesPath)) {
      const size = (fs.statSync(mainRulesPath).size / 1024).toFixed(1);
      console.log(`✅ 主规则文件: .cursorrules (${size}KB)`);
    } else {
      console.log('❌ 主规则文件不存在: .cursorrules');
    }

    // 检查分片规则文件
    console.log('\n📁 分片规则文件:');
    const ruleFiles = [
      'rules-ai.md',
      'rules-education.md',
      'rules-performance.md',
      'rules-security.md'
    ];

    ruleFiles.forEach(file => {
      const filePath = path.join(this.cursorPath, file);
      if (fs.existsSync(filePath)) {
        const size = (fs.statSync(filePath).size / 1024).toFixed(1);
        console.log(`  ✅ ${file} (${size}KB)`);
      } else {
        console.log(`  ❌ ${file} - 不存在`);
      }
    });

    // 检查扩展规则文件
    console.log('\n📄 扩展规则文件:');
    Object.keys(this.extractionRules).forEach(file => {
      const filePath = path.join(this.cursorPath, file);
      if (fs.existsSync(filePath)) {
        const size = (fs.statSync(filePath).size / 1024).toFixed(1);
        const mtime = fs.statSync(filePath).mtime.toISOString().split('T')[0];
        console.log(`  ✅ ${file} (${size}KB, 更新: ${mtime})`);
      } else {
        console.log(`  ❌ ${file} - 不存在`);
      }
    });

    // 统计总大小
    let totalSize = 0;
    if (fs.existsSync(this.cursorPath)) {
      fs.readdirSync(this.cursorPath).forEach(file => {
        const filePath = path.join(this.cursorPath, file);
        if (fs.statSync(filePath).isFile()) {
          totalSize += fs.statSync(filePath).size;
        }
      });
    }

    console.log(`\n📊 总计: ${(totalSize / 1024).toFixed(1)}KB`);

    if (totalSize > 50 * 1024) {
      console.log('⚠️  警告: 规则文件总大小超过50KB，可能影响Cursor性能');
    } else {
      console.log('✅ 规则文件大小合理');
    }
  }

  /**
   * 主执行函数
   */
  run() {
    const args = process.argv.slice(2);

    if (args.includes('--help') || args.includes('-h')) {
      console.log(`
Cursor 文档助手 - 使用说明

命令:
  --update          更新所有规则文件
  --prompt <shortcut>  生成Chat提示模板
  --status          检查规则文件状态
  --help            显示帮助信息

快捷方式:
  ${Object.keys(this.shortcuts).join(', ')}

示例:
  node scripts/cursor-docs-helper.js --update
  node scripts/cursor-docs-helper.js --prompt @ai-rules
  node scripts/cursor-docs-helper.js --status
      `);
      return;
    }

    if (args.includes('--update')) {
      this.generateExtendedRules();
      this.createQuickReference();
      console.log('\n🎉 规则文件更新完成！');
      return;
    }

    if (args.includes('--status')) {
      this.checkStatus();
      return;
    }

    const promptIndex = args.indexOf('--prompt');
    if (promptIndex !== -1 && args[promptIndex + 1]) {
      const shortcut = args[promptIndex + 1];
      const prompt = this.generateChatPrompt(shortcut);
      if (prompt) {
        console.log('📝 生成的Chat提示:\n');
        console.log(prompt);
      }
      return;
    }

    // 默认行为：更新规则文件
    console.log('🚀 Cursor 文档助手启动...\n');
    this.generateExtendedRules();
    this.createQuickReference();
    this.checkStatus();
    console.log('\n🎉 完成！现在可以在Cursor中使用这些规则文件了。');
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  const helper = new CursorDocsHelper();
  helper.run();
}

module.exports = CursorDocsHelper;
