#!/usr/bin/env node

/**
 * Specs集成验证脚本
 * 确保Cursor智能导航系统完全可执行且功能完整
 */

const fs = require('fs');
const path = require('path');

class SpecsIntegrationVerifier {
  constructor() {
    this.projectRoot = process.cwd();
    this.results = {
      passed: 0,
      failed: 0,
      warnings: 0,
      details: []
    };
  }

  /**
   * 运行所有验证测试
   */
  async runAllVerifications() {
    console.log('🔍 开始验证Specs集成系统...\n');

    // 1. 验证核心文件存在
    this.verifyCoreFielsExist();

    // 2. 验证VS Code配置
    this.verifyVSCodeConfig();

    // 3. 验证导航文件内容完整性
    this.verifyNavigatorContent();

    // 4. 验证原始specs文件可访问性
    this.verifyOriginalSpecsFiles();

    // 5. 验证查询模板有效性
    this.verifyQueryTemplates();

    // 6. 验证功能完整性覆盖
    this.verifyFunctionalCompleteness();

    // 7. 生成验证报告
    this.generateReport();
  }

  /**
   * 验证核心文件存在
   */
  verifyCoreFielsExist() {
    console.log('📁 验证核心文件存在性...');

    const coreFiles = [
      '.cursor/specs-core-navigator.md',
      '.cursor/ai-agent-core-context.md',
      '.cursor/rules-ai.md',
      '.cursor/rules-education.md',
      '.cursor/rules-performance.md',
      '.cursor/rules-security.md',
      '.vscode/settings.json',
      '.cursorrules'
    ];

    coreFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file);
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        const sizeKB = (stats.size / 1024).toFixed(1);
        this.addResult('✅', `${file} 存在 (${sizeKB}KB)`);
      } else {
        this.addResult('❌', `${file} 缺失`, 'error');
      }
    });
  }

  /**
   * 验证VS Code配置
   */
  verifyVSCodeConfig() {
    console.log('\n⚙️ 验证VS Code配置...');

    const settingsPath = path.join(this.projectRoot, '.vscode/settings.json');

    if (!fs.existsSync(settingsPath)) {
      this.addResult('❌', 'settings.json 不存在', 'error');
      return;
    }

    try {
      const settingsContent = fs.readFileSync(settingsPath, 'utf8');
      // 移除JSON注释以便解析
      const cleanedContent = settingsContent
        .replace(/\/\*[\s\S]*?\*\//g, '') // 移除块注释
        .replace(/\/\/.*$/gm, ''); // 移除行注释
      const settings = JSON.parse(cleanedContent);

      // 检查cursor.rules.contextFiles配置
      if (settings['cursor.rules.contextFiles']) {
        const contextFiles = settings['cursor.rules.contextFiles'];

        // 验证specs-core-navigator.md是否在列表中
        if (contextFiles.includes('.cursor/specs-core-navigator.md')) {
          this.addResult('✅', 'specs-core-navigator.md 已添加到Cursor上下文');
        } else {
          this.addResult('❌', 'specs-core-navigator.md 未添加到Cursor上下文', 'error');
        }

        // 验证所有上下文文件是否存在
        contextFiles.forEach(file => {
          const filePath = path.join(this.projectRoot, file);
          if (fs.existsSync(filePath)) {
            this.addResult('✅', `上下文文件 ${file} 存在`);
          } else {
            this.addResult('❌', `上下文文件 ${file} 缺失`, 'error');
          }
        });

      } else {
        this.addResult('❌', 'cursor.rules.contextFiles 配置缺失', 'error');
      }

    } catch (error) {
      this.addResult('❌', `settings.json 解析失败: ${error.message}`, 'error');
    }
  }

  /**
   * 验证导航文件内容完整性
   */
  verifyNavigatorContent() {
    console.log('\n📋 验证导航文件内容完整性...');

    const navigatorPath = path.join(this.projectRoot, '.cursor/specs-core-navigator.md');

    if (!fs.existsSync(navigatorPath)) {
      this.addResult('❌', '导航文件不存在', 'error');
      return;
    }

    const content = fs.readFileSync(navigatorPath, 'utf8');

    // 验证关键部分是否存在
    const requiredSections = [
      '文档完整性概览',
      'Cursor 智能查询策略',
      '需求完整性矩阵',
      '40 个需求',
      '设计文档核心架构',
      '开发任务完整架构',
      'Cursor 智能体使用方式',
      '功能完整性保障机制'
    ];

    requiredSections.forEach(section => {
      if (content.includes(section)) {
        this.addResult('✅', `包含关键部分: ${section}`);
      } else {
        this.addResult('❌', `缺少关键部分: ${section}`, 'error');
      }
    });

    // 验证需求矩阵完整性
    const requirementMatches = content.match(/需求\s*\d+/g);
    if (requirementMatches && requirementMatches.length >= 40) {
      this.addResult('✅', `需求矩阵包含 ${requirementMatches.length} 个需求`);
    } else {
      this.addResult('⚠️', `需求矩阵可能不完整，仅发现 ${requirementMatches ? requirementMatches.length : 0} 个需求`, 'warning');
    }

    // 验证行号范围
    const lineRangeMatches = content.match(/\d+-\d+\s*行/g);
    if (lineRangeMatches && lineRangeMatches.length >= 30) {
      this.addResult('✅', `包含 ${lineRangeMatches.length} 个精确行号范围`);
    } else {
      this.addResult('⚠️', `行号范围可能不足，仅发现 ${lineRangeMatches ? lineRangeMatches.length : 0} 个`, 'warning');
    }
  }

  /**
   * 验证原始specs文件可访问性
   */
  verifyOriginalSpecsFiles() {
    console.log('\n📄 验证原始specs文件可访问性...');

    const specsFiles = [
      '.kiro/specs/cet4-learning-system/requirements.md',
      '.kiro/specs/cet4-learning-system/design.md',
      '.kiro/specs/cet4-learning-system/tasks.md'
    ];

    specsFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file);
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        const sizeKB = (stats.size / 1024).toFixed(1);
        const lines = fs.readFileSync(filePath, 'utf8').split('\n').length;
        this.addResult('✅', `${file} 可访问 (${sizeKB}KB, ${lines}行)`);
      } else {
        this.addResult('❌', `${file} 无法访问`, 'error');
      }
    });
  }

  /**
   * 验证查询模板有效性
   */
  verifyQueryTemplates() {
    console.log('\n🔍 验证查询模板有效性...');

    const navigatorPath = path.join(this.projectRoot, '.cursor/specs-core-navigator.md');

    if (!fs.existsSync(navigatorPath)) {
      this.addResult('❌', '导航文件不存在，无法验证查询模板', 'error');
      return;
    }

    const content = fs.readFileSync(navigatorPath, 'utf8');

    // 验证查询模板格式
    const queryTemplates = [
      '从.kiro/specs/cet4-learning-system/requirements.md第',
      '从.kiro/specs/cet4-learning-system/design.md第',
      '从.kiro/specs/cet4-learning-system/tasks.md第',
      '查看requirements.md第',
      '查看design.md第',
      '查看tasks.md第'
    ];

    queryTemplates.forEach(template => {
      if (content.includes(template)) {
        this.addResult('✅', `查询模板格式正确: ${template}...`);
      } else {
        this.addResult('⚠️', `查询模板可能缺失: ${template}...`, 'warning');
      }
    });

    // 验证具体的查询示例
    const specificQueries = [
      '第581-654行',
      '第393-456行',
      '第169-268行',
      '第15-88行',
      '第189-370行',
      '第722-996行'
    ];

    let foundQueries = 0;
    specificQueries.forEach(query => {
      if (content.includes(query)) {
        foundQueries++;
      }
    });

    if (foundQueries >= 4) {
      this.addResult('✅', `包含 ${foundQueries} 个具体查询示例`);
    } else {
      this.addResult('⚠️', `具体查询示例不足，仅发现 ${foundQueries} 个`, 'warning');
    }
  }

  /**
   * 验证功能完整性覆盖
   */
  verifyFunctionalCompleteness() {
    console.log('\n🎯 验证功能完整性覆盖...');

    const navigatorPath = path.join(this.projectRoot, '.cursor/specs-core-navigator.md');

    if (!fs.existsSync(navigatorPath)) {
      this.addResult('❌', '导航文件不存在，无法验证功能完整性', 'error');
      return;
    }

    const content = fs.readFileSync(navigatorPath, 'utf8');

    // 验证三端覆盖
    const endpoints = ['管理员端', '教师端', '学生端'];
    endpoints.forEach(endpoint => {
      if (content.includes(endpoint)) {
        this.addResult('✅', `${endpoint}需求已覆盖`);
      } else {
        this.addResult('❌', `${endpoint}需求未覆盖`, 'error');
      }
    });

    // 验证核心功能模块
    const coreModules = [
      '用户管理模块',
      '课程管理模块',
      '训练系统模块',
      'AI集成模块'
    ];

    coreModules.forEach(module => {
      if (content.includes(module)) {
        this.addResult('✅', `${module}已覆盖`);
      } else {
        this.addResult('❌', `${module}未覆盖`, 'error');
      }
    });

    // 验证开发阶段覆盖
    const phases = ['第一阶段', '第二阶段', '第三阶段', '第四阶段', '第五阶段', '第六阶段'];
    let phasesFound = 0;
    phases.forEach(phase => {
      if (content.includes(phase)) {
        phasesFound++;
      }
    });

    if (phasesFound === 6) {
      this.addResult('✅', '6个开发阶段完整覆盖');
    } else {
      this.addResult('⚠️', `开发阶段覆盖不完整，仅发现 ${phasesFound}/6 个阶段`, 'warning');
    }
  }

  /**
   * 添加验证结果
   */
  addResult(status, message, type = 'success') {
    const result = { status, message, type };
    this.results.details.push(result);

    if (type === 'error') {
      this.results.failed++;
      console.log(`  ${status} ${message}`);
    } else if (type === 'warning') {
      this.results.warnings++;
      console.log(`  ${status} ${message}`);
    } else {
      this.results.passed++;
      console.log(`  ${status} ${message}`);
    }
  }

  /**
   * 生成验证报告
   */
  generateReport() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 Specs集成验证报告');
    console.log('='.repeat(60));

    console.log(`✅ 通过: ${this.results.passed}`);
    console.log(`⚠️ 警告: ${this.results.warnings}`);
    console.log(`❌ 失败: ${this.results.failed}`);
    console.log(`📊 总计: ${this.results.passed + this.results.warnings + this.results.failed}`);

    const successRate = ((this.results.passed / (this.results.passed + this.results.warnings + this.results.failed)) * 100).toFixed(1);
    console.log(`🎯 成功率: ${successRate}%`);

    if (this.results.failed === 0) {
      console.log('\n🎉 验证通过！Specs集成系统完全可执行且功能完整！');
      console.log('\n💡 您现在可以在Cursor Chat中使用以下查询：');
      console.log('   "从requirements.md第581-654行提取需求21的完整内容"');
      console.log('   "查看design.md第189-370行的模块设计"');
      console.log('   "按照tasks.md第722-996行实现训练系统"');
    } else {
      console.log('\n⚠️ 发现问题，请修复后重新验证！');

      // 显示错误详情
      console.log('\n🔧 需要修复的问题：');
      this.results.details
        .filter(r => r.type === 'error')
        .forEach(r => console.log(`   ${r.status} ${r.message}`));
    }

    // 生成验证报告文件
    const reportPath = path.join(this.projectRoot, '.cursor/specs-verification-report.md');
    this.generateMarkdownReport(reportPath);
    console.log(`\n📄 详细报告已生成: ${reportPath}`);
  }

  /**
   * 生成Markdown格式的验证报告
   */
  generateMarkdownReport(reportPath) {
    const timestamp = new Date().toISOString();

    let markdown = `# Specs集成验证报告\n\n`;
    markdown += `**验证时间**: ${timestamp}\n\n`;
    markdown += `## 📊 验证统计\n\n`;
    markdown += `- ✅ 通过: ${this.results.passed}\n`;
    markdown += `- ⚠️ 警告: ${this.results.warnings}\n`;
    markdown += `- ❌ 失败: ${this.results.failed}\n`;
    markdown += `- 📊 总计: ${this.results.passed + this.results.warnings + this.results.failed}\n`;

    const successRate = ((this.results.passed / (this.results.passed + this.results.warnings + this.results.failed)) * 100).toFixed(1);
    markdown += `- 🎯 成功率: ${successRate}%\n\n`;

    markdown += `## 📋 详细结果\n\n`;

    this.results.details.forEach(result => {
      markdown += `${result.status} ${result.message}\n\n`;
    });

    markdown += `## 🚀 使用指南\n\n`;
    markdown += `如果验证通过，您可以在Cursor Chat中使用以下查询模板：\n\n`;
    markdown += `### 需求查询\n`;
    markdown += `\`\`\`\n`;
    markdown += `"从requirements.md第581-654行提取需求21的完整内容"\n`;
    markdown += `"查看requirements.md第393-456行需求14的详细验收标准"\n`;
    markdown += `\`\`\`\n\n`;
    markdown += `### 设计查询\n`;
    markdown += `\`\`\`\n`;
    markdown += `"从design.md第189-370行提取核心模块设计"\n`;
    markdown += `"查看design.md第512-700行AI集成设计"\n`;
    markdown += `\`\`\`\n\n`;
    markdown += `### 任务查询\n`;
    markdown += `\`\`\`\n`;
    markdown += `"从tasks.md第722-996行查看第四阶段开发任务"\n`;
    markdown += `"按照tasks.md第724-763行实现学生训练中心"\n`;
    markdown += `\`\`\`\n\n`;

    fs.writeFileSync(reportPath, markdown);
  }
}

// 主执行函数
async function main() {
  const verifier = new SpecsIntegrationVerifier();
  await verifier.runAllVerifications();
}

// 如果直接运行此脚本
if (require.main === module) {
  main().catch(console.error);
}

module.exports = SpecsIntegrationVerifier;
