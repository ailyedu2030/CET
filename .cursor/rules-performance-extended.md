# performance - 扩展规则

## 📋 来源: realtime-response-strategy.md

# 实时响应策略配置指南

## 🎯 实时性需求分析

### 🚨 极高实时性（<3 秒，必须立即响应）

- **功能**：学生完成训练后的即时批改
- **要求**：批改响应时间<3 秒，反馈详细度>85%
- **用户体验**：学生做完作业立即看到结果和解析
- **配置策略**：使用流式输出，实时显示批改进度
- **功能**：写作训练中的语法检查、词汇建议、句式优化
- **要求**：实时响应用户输入
- **用户体验**：打字时即时提示和纠错
- **配置策略**：使用流式输出，边输入边提示
- **功能**：实时字幕、跟读练习反馈
- **要求**：音频播放同步显示
- **用户体验**：无延迟的听力辅助
- **配置策略**：使用流式输出，同步音频进度

### ⚡ 高实时性（<5 秒，快速响应）

- **功能**：教师配置参数后生成训练题目
- **要求**：题目生成<2 秒
- **用户体验**：快速获得训练内容
- **配置策略**：非流式输出，但高优先级处理
- **功能**：实时查询学生学习状态、注册状态
- **要求**：查询响应<1 秒
- **用户体验**：即时获取状态信息
- **配置策略**：缓存+实时更新机制
- **功能**：实时监控系统状态、安全事件
- **要求**：异常检测<5 秒内告警
- **用户体验**：及时发现和处理问题
- **配置策略**：实时数据流处理

### 🕐 中等实时性（可错峰处理）

- **功能**：AI 分析学生学习数据，生成详细报告
- **要求**：分析<5 秒，但可延迟处理
- **用户体验**：详细分析结果，不要求即时
- **配置策略**：错峰调度，使用推理模型
- **功能**：基于教材和考纲生成教学内容
- **要求**：质量优先，时间可接受
- **用户体验**：高质量内容生成
- **配置策略**：错峰调度，深度推理
- **功能**：生成各类统计报表和分析报告
- **要求**：准确性优先
- **用户体验**：定期获取详细报告
- **配置策略**：批量处理，错峰执行

## 🔧 技术实现策略

### 流式输出配置

```
class StreamingResponseConfig:
    """流式输出配置"""

    # 极高实时性场景 - 使用流式输出
    STREAMING_SCENARIOS = {
        "writing_grading": {
            "model": "deepseek-chat",  # 标准模型足够快
            "temperature": 1.0,        # 数据分析场景，使用官方推荐温度
            "max_tokens": 2000,
            "stream": True,  # 启用流式输出
```

## 📊 实时批改系统配置

### 流式批改实现

```
class RealtimeGradingService:
    """实时批改服务 - 专门处理学生作业的即时批改"""

    def __init__(self):
        self.deepseek_service = OptimizedDeepSeekService()
        self.grading_cache = GradingCache()
        self.performance_monitor = RealtimePerformanceMonitor()

    async def stream_writing_grading(
        self,
```

## 📋 配置总结

### 实时性配置矩阵

| 智能批改 | <3 秒 | 流式 | deepseek-chat | 1.0 | 数据分析 | urgent | 否 |
| 实时辅助 | <1 秒 | 流式 | deepseek-chat | 1.3 | 通用对话 | urgent | 否 |
| 听力字幕 | <1 秒 | 流式 | deepseek-chat | 1.3 | 翻译场景 | urgent | 否 |
| 题目生成 | <2 秒 | 非流式 | deepseek-chat | 1.5 | 创意写作 | high | 否 |
| 快速分析 | <5 秒 | 非流式 | deepseek-chat | 1.0 | 数据分析 | high | 否 |
| 学情分析 | <5 秒 | 非流式 | deepseek-reasoner | 1.0 | 数据分析 | normal | 是 |
| 大纲生成 | 可延迟 | 非流式 | deepseek-reasoner | 1.5 | 创意写作 | cost_sensitive | 是 |

### 温度参数优化（基于 DeepSeek 官方建议）

- **批改系统（1.0）**：数据分析场景，分析学生作文并提供评分和建议
- **实时辅助（1.3）**：通用对话场景，提供写作建议和语法纠错
- **听力字幕（1.3）**：翻译场景，将音频内容转换为文字字幕
- **题目生成（1.5）**：创意类写作场景，生成多样化的训练题目
- **数据分析（1.0）**：数据分析场景，分析学习数据和生成报告
- **大纲生成（1.5）**：创意类写作场景，生成教学大纲和教案内容

### 成本优化效果

- **实时功能成本**：约占总成本的 60%（必要投入）
- **错峰优化节省**：非实时功能节省 40-60%成本
- **缓存优化节省**：重复请求节省 75%成本
- **总体优化效果**：在保证用户体验的前提下节省 30%成本

## 📋 来源: realtime-performance-testing.md

# 实时性能测试配置指南

## 🎯 测试目标

确保英语四级学习系统的实时功能满足用户体验要求，特别是智能批改和实时辅助功能的响应时间和稳定性。

## 📊 性能基准要求

### 实时性能指标

| 功能场景 | 响应时间要求 | 成功率要求 | 并发用户 | 测试持续时间 |
| 智能批改 | <3 秒 | >95% | 500 用户 | 30 分钟 |
| 实时辅助 | <1 秒 | >98% | 200 用户 | 60 分钟 |
| 听力字幕 | <1 秒 | >99% | 100 用户 | 30 分钟 |
| 题目生成 | <2 秒 | >95% | 300 用户 | 15 分钟 |
| 学情分析 | <5 秒 | >90% | 100 用户 | 10 分钟 |

### 流式输出性能要求

- **首字节时间**：<500ms
- **流式间隔**：<200ms
- **完整响应时间**：符合上表要求
- **连接稳定性**：>99.5%
- **重连成功率**：>95%

## 🧪 测试用例设计

### 1. 流式批改性能测试

```
# tests/performance/test_streaming_grading.py
import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

class StreamingGradingPerformanceTest:
    """流式批改性能测试"""

```

# tests/performance/test_realtime_assist.py

    """实时写作辅助性能测试"""
                    # 验证实时辅助响应时间
                    assert response_time < 1.0, f"实时辅助响应时间超标: {response_time}s"
        assert avg_response_time < 0.8, f"平均响应时间超标: {avg_response_time}s"
        """测试防抖机制性能"""
        # 快速发送请求（间隔100ms）
            await asyncio.sleep(0.1)  # 100ms间隔

### 3. 系统压力测试

```
# tests/performance/test_system_stress.py
class SystemStressTest:
    """系统压力测试"""

    async def test_mixed_workload_stress(self):
        """混合工作负载压力测试"""

        # 定义不同类型的工作负载
        workloads = {
            'grading': {'weight': 0.4, 'concurrent': 200},      # 40%批改请求
```

# app/monitoring/realtime_dashboard.py

    """实时性能监控面板"""
        """获取实时性能指标"""
            time_score = max(0, 100 - (response_time * 50))  # 2秒=0分

### 性能测试报告生成

```
# tests/performance/report_generator.py
class PerformanceReportGenerator:
    """性能测试报告生成器"""

    def generate_comprehensive_report(self, test_results: Dict) -> str:
        """生成综合性能测试报告"""

        report = f"""
# 英语四级学习系统实时性能测试报告

```

## 🚨 性能告警配置

### 告警规则

```
performance_alerts:
  critical:
    - metric: "grading_response_time"
      threshold: 5.0
      duration: "2m"
      action: "immediate_notification"

    - metric: "assist_success_rate"
      threshold: 0.90
      duration: "1m"
```

这个性能测试配置确保了：

1. **全面的性能测试覆盖**：单次、并发、压力、混合负载测试
2. **严格的性能基准**：明确的响应时间和成功率要求
3. **实时监控面板**：系统健康状态和性能趋势监控
4. **自动化告警**：性能异常时及时通知
5. **详细的测试报告**：性能分析和优化建议
