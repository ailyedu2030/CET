#!/usr/bin/env node

/**
 * Cursor Rules 功能测试脚本
 * 验证 Cursor 规则文件是否正常工作
 */

const fs = require('fs');
const path = require('path');

class CursorRulesTest {
  constructor() {
    this.projectRoot = process.cwd();
    this.cursorPath = path.join(this.projectRoot, '.cursor');
    this.results = {
      passed: 0,
      failed: 0,
      tests: []
    };
  }

  // 测试文件存在性
  testFileExistence() {
    console.log('🔍 测试规则文件存在性...');

    const requiredFiles = [
      '.cursorrules',
      '.cursor/ai-agent-core-context.md',
      '.cursor/rules-ai.md',
      '.cursor/rules-education.md',
      '.cursor/rules-performance.md',
      '.cursor/rules-security.md'
    ];

    requiredFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file);
      const exists = fs.existsSync(filePath);

      this.addTest(`文件存在: ${file}`, exists, exists ? '✅' : '❌ 文件不存在');
    });
  }

  // 测试文件大小
  testFileSize() {
    console.log('📏 测试文件大小...');

    const sizeTests = [
      { file: '.cursorrules', maxSize: 5 * 1024, name: '主规则文件' },
      { file: '.cursor/rules-security.md', maxSize: 8 * 1024, name: '安全规则文件' },
      { file: '.cursor/ai-agent-core-context.md', maxSize: 6 * 1024, name: '智能体核心上下文' }
    ];

    sizeTests.forEach(test => {
      const filePath = path.join(this.projectRoot, test.file);
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        const sizeKB = Math.round(stats.size / 1024 * 100) / 100;
        const passed = stats.size <= test.maxSize;

        this.addTest(
          `${test.name}大小 (${sizeKB}KB)`,
          passed,
          passed ? `✅ ${sizeKB}KB` : `❌ ${sizeKB}KB 超过限制 ${test.maxSize/1024}KB`
        );
      }
    });
  }

  // 测试内容完整性
  testContentIntegrity() {
    console.log('📋 测试内容完整性...');

    const contentTests = [
      {
        file: '.cursor/rules-ai.md',
        keywords: ['DeepSeek', 'AI服务', '批改', '温度参数'],
        name: 'AI规则内容'
      },
      {
        file: '.cursor/rules-education.md',
        keywords: ['教育', '学生', '未成年人', '数据保护'],
        name: '教育规则内容'
      },
      {
        file: '.cursor/rules-security.md',
        keywords: ['JWT', '认证', '加密', '权限'],
        name: '安全规则内容'
      },
      {
        file: '.cursor/ai-agent-core-context.md',
        keywords: ['智能体', '模块边界', '检查清单', '提示词'],
        name: '智能体上下文内容'
      }
    ];

    contentTests.forEach(test => {
      const filePath = path.join(this.projectRoot, test.file);
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf8');
        const missingKeywords = test.keywords.filter(keyword =>
          !content.includes(keyword)
        );

        const passed = missingKeywords.length === 0;
        this.addTest(
          `${test.name}完整性`,
          passed,
          passed ? '✅ 关键内容完整' : `❌ 缺失关键词: ${missingKeywords.join(', ')}`
        );
      }
    });
  }

  // 测试 VS Code 配置
  testVSCodeConfig() {
    console.log('⚙️ 测试 VS Code 配置...');

    const settingsPath = path.join(this.projectRoot, '.vscode/settings.json');
    if (fs.existsSync(settingsPath)) {
      try {
        const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
        const contextFiles = settings['cursor.rules.contextFiles'];

        // 检查是否包含核心上下文文件
        const hasCoreContext = contextFiles && contextFiles.includes('.cursor/ai-agent-core-context.md');
        this.addTest(
          'VS Code 配置包含智能体核心上下文',
          hasCoreContext,
          hasCoreContext ? '✅ 配置正确' : '❌ 缺少核心上下文配置'
        );

        // 检查配置文件数量
        const expectedCount = 5; // 包括核心上下文的5个文件
        const actualCount = contextFiles ? contextFiles.length : 0;
        const correctCount = actualCount === expectedCount;

        this.addTest(
          `VS Code 配置文件数量 (${actualCount}/${expectedCount})`,
          correctCount,
          correctCount ? '✅ 文件数量正确' : `❌ 期望${expectedCount}个，实际${actualCount}个`
        );

      } catch (error) {
        this.addTest('VS Code 配置文件解析', false, `❌ JSON解析错误: ${error.message}`);
      }
    } else {
      this.addTest('VS Code 配置文件存在', false, '❌ settings.json 不存在');
    }
  }

  // 生成使用示例测试
  testUsageExamples() {
    console.log('💡 生成使用示例...');

    const examples = [
      {
        scenario: '实现用户认证功能',
        prompt: '基于英语四级学习系统的完整规范，实现用户JWT认证功能。请确保遵循安全规范和模块化架构约束。',
        expectedFiles: ['.cursor/ai-agent-core-context.md', '.cursor/rules-security.md']
      },
      {
        scenario: '实现AI批改系统',
        prompt: '根据AI服务规范，实现DeepSeek智能批改功能。请包含流式输出和降级策略。',
        expectedFiles: ['.cursor/rules-ai.md', '.cursor/ai-agent-core-context.md']
      },
      {
        scenario: '实现学生训练模块',
        prompt: '基于教育系统要求，实现学生综合训练中心。请确保符合未成年人保护和数据安全要求。',
        expectedFiles: ['.cursor/rules-education.md', '.cursor/ai-agent-core-context.md']
      }
    ];

    console.log('\n📝 Cursor Chat 使用示例：');
    examples.forEach((example, index) => {
      console.log(`\n${index + 1}. ${example.scenario}`);
      console.log(`   提示词: "${example.prompt}"`);
      console.log(`   相关文件: ${example.expectedFiles.join(', ')}`);
    });

    this.addTest('使用示例生成', true, '✅ 示例已生成');
  }

  // 添加测试结果
  addTest(name, passed, message) {
    this.tests.push({ name, passed, message });
    if (passed) {
      this.results.passed++;
    } else {
      this.results.failed++;
    }
  }

  // 运行所有测试
  async runAllTests() {
    console.log('🚀 开始 Cursor Rules 功能测试...\n');

    this.testFileExistence();
    this.testFileSize();
    this.testContentIntegrity();
    this.testVSCodeConfig();
    this.testUsageExamples();

    this.generateReport();
  }

  // 生成测试报告
  generateReport() {
    console.log('\n📊 测试报告');
    console.log('='.repeat(50));

    this.tests.forEach(test => {
      console.log(`${test.passed ? '✅' : '❌'} ${test.name}: ${test.message}`);
    });

    console.log('\n📈 测试统计');
    console.log(`总测试数: ${this.tests.length}`);
    console.log(`通过: ${this.results.passed}`);
    console.log(`失败: ${this.results.failed}`);
    console.log(`成功率: ${Math.round(this.results.passed / this.tests.length * 100)}%`);

    // 生成状态报告
    const status = this.results.failed === 0 ? '🎉 所有测试通过！' : '⚠️ 存在问题需要修复';
    console.log(`\n${status}`);

    if (this.results.failed === 0) {
      console.log('\n✅ Cursor Rules 配置正常工作！');
      console.log('现在可以在 Cursor 中使用智能体进行自动化开发了。');
    } else {
      console.log('\n❌ 请修复上述问题后重新测试。');
    }

    // 保存报告到文件
    const reportPath = path.join(this.cursorPath, 'test-report.md');
    this.saveReport(reportPath);
  }

  // 保存报告到文件
  saveReport(filePath) {
    const report = `# Cursor Rules 测试报告

## 测试结果
- 总测试数: ${this.tests.length}
- 通过: ${this.results.passed}
- 失败: ${this.results.failed}
- 成功率: ${Math.round(this.results.passed / this.tests.length * 100)}%

## 详细结果
${this.tests.map(test => `- ${test.passed ? '✅' : '❌'} ${test.name}: ${test.message}`).join('\n')}

## 测试时间
${new Date().toLocaleString()}

## 使用建议
${this.results.failed === 0 ?
  '✅ 配置正常，可以开始使用 Cursor 智能体进行开发。' :
  '❌ 请修复上述问题后重新测试。'}
`;

    try {
      fs.writeFileSync(filePath, report);
      console.log(`\n📄 详细报告已保存到: ${filePath}`);
    } catch (error) {
      console.log(`\n❌ 保存报告失败: ${error.message}`);
    }
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  const tester = new CursorRulesTest();
  tester.runAllTests();
}

module.exports = CursorRulesTest;
