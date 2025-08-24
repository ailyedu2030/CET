---
inclusion: always
---

# 实时性能测试配置指南

## 🎯 测试目标

确保英语四级学习系统的实时功能满足用户体验要求，特别是智能批改和实时辅助功能的响应时间和稳定性。

## 📊 性能基准要求

### 实时性能指标

| 功能场景 | 响应时间要求 | 成功率要求 | 并发用户 | 测试持续时间 |
|---------|-------------|-----------|---------|-------------|
| 智能批改 | <3秒 | >95% | 500用户 | 30分钟 |
| 实时辅助 | <1秒 | >98% | 200用户 | 60分钟 |
| 听力字幕 | <1秒 | >99% | 100用户 | 30分钟 |
| 题目生成 | <2秒 | >95% | 300用户 | 15分钟 |
| 学情分析 | <5秒 | >90% | 100用户 | 10分钟 |

### 流式输出性能要求

- **首字节时间**：<500ms
- **流式间隔**：<200ms
- **完整响应时间**：符合上表要求
- **连接稳定性**：>99.5%
- **重连成功率**：>95%

## 🧪 测试用例设计

### 1. 流式批改性能测试

```python
# tests/performance/test_streaming_grading.py
import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

class StreamingGradingPerformanceTest:
    """流式批改性能测试"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_writings = self._load_test_writings()
        self.performance_metrics = []
    
    async def test_single_grading_performance(self):
        """单次批改性能测试"""
        
        writing_content = self.test_writings[0]
        start_time = time.time()
        
        # 建立SSE连接
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/grading/stream",
                params={
                    "submission_id": "test_001",
                    "question_type": "argumentative"
                }
            ) as response:
                
                first_byte_time = None
                chunks_received = 0
                chunk_intervals = []
                last_chunk_time = start_time
                
                async for line in response.content:
                    current_time = time.time()
                    
                    if first_byte_time is None:
                        first_byte_time = current_time - start_time
                    
                    if chunks_received > 0:
                        interval = current_time - last_chunk_time
                        chunk_intervals.append(interval)
                    
                    chunks_received += 1
                    last_chunk_time = current_time
                
                total_time = time.time() - start_time
                
                # 记录性能指标
                metrics = {
                    'total_time': total_time,
                    'first_byte_time': first_byte_time,
                    'chunks_received': chunks_received,
                    'avg_chunk_interval': sum(chunk_intervals) / len(chunk_intervals) if chunk_intervals else 0,
                    'max_chunk_interval': max(chunk_intervals) if chunk_intervals else 0
                }
                
                # 验证性能要求
                assert total_time < 3.0, f"批改总时间超标: {total_time}s"
                assert first_byte_time < 0.5, f"首字节时间超标: {first_byte_time}s"
                assert metrics['avg_chunk_interval'] < 0.2, f"平均流式间隔超标: {metrics['avg_chunk_interval']}s"
                
                return metrics
    
    async def test_concurrent_grading_performance(self, concurrent_users: int = 100):
        """并发批改性能测试"""
        
        async def single_user_test(user_id: int):
            try:
                start_time = time.time()
                
                # 模拟用户提交批改请求
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/api/grading/stream",
                        params={
                            "submission_id": f"test_{user_id:03d}",
                            "question_type": "argumentative"
                        }
                    ) as response:
                        
                        chunks = []
                        async for line in response.content:
                            chunks.append(line)
                        
                        total_time = time.time() - start_time
                        
                        return {
                            'user_id': user_id,
                            'success': True,
                            'response_time': total_time,
                            'chunks_count': len(chunks)
                        }
                        
            except Exception as e:
                return {
                    'user_id': user_id,
                    'success': False,
                    'error': str(e),
                    'response_time': time.time() - start_time
                }
        
        # 并发执行测试
        tasks = [single_user_test(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 分析结果
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get('success')]
        
        success_rate = len(successful_results) / len(results)
        avg_response_time = sum(r['response_time'] for r in successful_results) / len(successful_results)
        
        # 验证并发性能要求
        assert success_rate >= 0.95, f"并发成功率不达标: {success_rate:.2%}"
        assert avg_response_time < 3.0, f"并发平均响应时间超标: {avg_response_time}s"
        
        return {
            'concurrent_users': concurrent_users,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'failed_count': len(failed_results)
        }
    
    def _load_test_writings(self) -> List[str]:
        """加载测试用的作文内容"""
        return [
            "In today's digital age, online learning has become increasingly popular...",
            "Environmental protection is one of the most pressing issues of our time...",
            "The role of artificial intelligence in education is rapidly evolving...",
            # 更多测试内容...
        ]

### 2. 实时写作辅助性能测试

```python
# tests/performance/test_realtime_assist.py
class RealtimeAssistPerformanceTest:
    """实时写作辅助性能测试"""
    
    async def test_typing_simulation(self):
        """模拟用户打字的实时辅助测试"""
        
        text_sequence = [
            "In today's",
            "In today's digital",
            "In today's digital age,",
            "In today's digital age, online",
            "In today's digital age, online learning",
            "In today's digital age, online learning has",
            "In today's digital age, online learning has become"
        ]
        
        response_times = []
        
        for i, text in enumerate(text_sequence):
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/writing/realtime-assist",
                    json={
                        "text": text,
                        "cursor_position": len(text)
                    }
                ) as response:
                    
                    suggestion = ""
                    async for chunk in response.content.iter_chunked(1024):
                        suggestion += chunk.decode()
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    # 验证实时辅助响应时间
                    assert response_time < 1.0, f"实时辅助响应时间超标: {response_time}s"
        
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.8, f"平均响应时间超标: {avg_response_time}s"
        
        return {
            'sequence_count': len(text_sequence),
            'avg_response_time': avg_response_time,
            'max_response_time': max(response_times),
            'all_response_times': response_times
        }
    
    async def test_debounce_mechanism(self):
        """测试防抖机制性能"""
        
        # 模拟快速连续输入
        rapid_inputs = [
            "Hello",
            "Hello w",
            "Hello wo",
            "Hello wor",
            "Hello worl",
            "Hello world"
        ]
        
        # 快速发送请求（间隔100ms）
        tasks = []
        for text in rapid_inputs:
            task = asyncio.create_task(self._send_assist_request(text))
            tasks.append(task)
            await asyncio.sleep(0.1)  # 100ms间隔
        
        # 等待所有请求完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证防抖效果（应该只有最后几个请求成功）
        successful_requests = [r for r in results if not isinstance(r, Exception)]
        
        # 防抖应该减少实际处理的请求数量
        assert len(successful_requests) < len(rapid_inputs), "防抖机制未生效"
        
        return {
            'total_requests': len(rapid_inputs),
            'successful_requests': len(successful_requests),
            'debounce_effectiveness': 1 - (len(successful_requests) / len(rapid_inputs))
        }

### 3. 系统压力测试

```python
# tests/performance/test_system_stress.py
class SystemStressTest:
    """系统压力测试"""
    
    async def test_mixed_workload_stress(self):
        """混合工作负载压力测试"""
        
        # 定义不同类型的工作负载
        workloads = {
            'grading': {'weight': 0.4, 'concurrent': 200},      # 40%批改请求
            'assist': {'weight': 0.3, 'concurrent': 150},       # 30%实时辅助
            'generation': {'weight': 0.2, 'concurrent': 100},   # 20%题目生成
            'analysis': {'weight': 0.1, 'concurrent': 50}       # 10%学情分析
        }
        
        async def execute_workload(workload_type: str, config: dict):
            tasks = []
            
            for i in range(config['concurrent']):
                if workload_type == 'grading':
                    task = self._execute_grading_request(i)
                elif workload_type == 'assist':
                    task = self._execute_assist_request(i)
                elif workload_type == 'generation':
                    task = self._execute_generation_request(i)
                elif workload_type == 'analysis':
                    task = self._execute_analysis_request(i)
                
                tasks.append(task)
            
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # 并发执行所有工作负载
        all_tasks = []
        for workload_type, config in workloads.items():
            task = execute_workload(workload_type, config)
            all_tasks.append(task)
        
        start_time = time.time()
        all_results = await asyncio.gather(*all_tasks)
        total_time = time.time() - start_time
        
        # 分析结果
        total_requests = sum(config['concurrent'] for config in workloads.values())
        successful_requests = 0
        
        for workload_results in all_results:
            for result in workload_results:
                if isinstance(result, dict) and result.get('success'):
                    successful_requests += 1
        
        success_rate = successful_requests / total_requests
        throughput = successful_requests / total_time
        
        # 验证系统压力测试要求
        assert success_rate >= 0.90, f"系统压力测试成功率不达标: {success_rate:.2%}"
        assert throughput >= 50, f"系统吞吐量不达标: {throughput:.1f} req/s"
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': success_rate,
            'total_time': total_time,
            'throughput': throughput
        }

## 📈 性能监控和报告

### 实时性能监控面板

```python
# app/monitoring/realtime_dashboard.py
class RealtimePerformanceDashboard:
    """实时性能监控面板"""
    
    def __init__(self):
        self.metrics_collector = RealtimePerformanceMonitor()
        self.alert_manager = AlertManager()
    
    async def get_realtime_metrics(self) -> Dict:
        """获取实时性能指标"""
        
        current_metrics = await self.metrics_collector.get_performance_metrics()
        
        # 计算关键指标
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._calculate_system_health(current_metrics),
            'realtime_functions': {
                'grading': {
                    'avg_response_time': current_metrics.get('writing_grading', {}).get('avg_response_time', 0),
                    'success_rate': current_metrics.get('writing_grading', {}).get('success_rate', 0),
                    'current_load': self._get_current_load('grading'),
                    'status': self._get_function_status('grading', current_metrics)
                },
                'assist': {
                    'avg_response_time': current_metrics.get('realtime_assist', {}).get('avg_response_time', 0),
                    'success_rate': current_metrics.get('realtime_assist', {}).get('success_rate', 0),
                    'current_load': self._get_current_load('assist'),
                    'status': self._get_function_status('assist', current_metrics)
                }
            },
            'alerts': await self.alert_manager.get_active_alerts(),
            'performance_trends': await self._get_performance_trends()
        }
        
        return dashboard_data
    
    def _calculate_system_health(self, metrics: Dict) -> str:
        """计算系统健康状态"""
        
        critical_functions = ['writing_grading', 'realtime_assist']
        health_scores = []
        
        for func in critical_functions:
            func_metrics = metrics.get(func, {})
            response_time = func_metrics.get('avg_response_time', float('inf'))
            success_rate = func_metrics.get('success_rate', 0)
            
            # 计算健康分数 (0-100)
            time_score = max(0, 100 - (response_time * 50))  # 2秒=0分
            success_score = success_rate * 100
            
            health_score = (time_score + success_score) / 2
            health_scores.append(health_score)
        
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        
        if avg_health >= 90:
            return 'excellent'
        elif avg_health >= 75:
            return 'good'
        elif avg_health >= 60:
            return 'warning'
        else:
            return 'critical'

### 性能测试报告生成

```python
# tests/performance/report_generator.py
class PerformanceReportGenerator:
    """性能测试报告生成器"""
    
    def generate_comprehensive_report(self, test_results: Dict) -> str:
        """生成综合性能测试报告"""
        
        report = f"""
# 英语四级学习系统实时性能测试报告

## 测试概览
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 测试环境: {self._get_test_environment()}
- 测试持续时间: {test_results.get('total_duration', 0):.1f}分钟

## 核心性能指标

### 智能批改系统
- 平均响应时间: {test_results.get('grading', {}).get('avg_response_time', 0):.2f}s (要求: <3s)
- 成功率: {test_results.get('grading', {}).get('success_rate', 0):.1%} (要求: >95%)
- 并发处理能力: {test_results.get('grading', {}).get('max_concurrent', 0)}用户
- 首字节时间: {test_results.get('grading', {}).get('first_byte_time', 0):.3f}s (要求: <0.5s)

### 实时写作辅助
- 平均响应时间: {test_results.get('assist', {}).get('avg_response_time', 0):.2f}s (要求: <1s)
- 成功率: {test_results.get('assist', {}).get('success_rate', 0):.1%} (要求: >98%)
- 防抖效果: {test_results.get('assist', {}).get('debounce_effectiveness', 0):.1%}

### 系统整体性能
- 总吞吐量: {test_results.get('system', {}).get('throughput', 0):.1f} req/s
- 系统健康度: {test_results.get('system', {}).get('health_score', 0):.1f}/100
- 资源使用率: CPU {test_results.get('system', {}).get('cpu_usage', 0):.1f}%, 内存 {test_results.get('system', {}).get('memory_usage', 0):.1f}%

## 性能优化建议

{self._generate_optimization_suggestions(test_results)}

## 风险评估

{self._generate_risk_assessment(test_results)}
"""
        
        return report
```

## 🚨 性能告警配置

### 告警规则

```yaml
performance_alerts:
  critical:
    - metric: "grading_response_time"
      threshold: 5.0
      duration: "2m"
      action: "immediate_notification"
    
    - metric: "assist_success_rate"
      threshold: 0.90
      duration: "1m"
      action: "immediate_notification"
  
  warning:
    - metric: "grading_response_time"
      threshold: 3.5
      duration: "5m"
      action: "delayed_notification"
    
    - metric: "system_throughput"
      threshold: 30
      duration: "10m"
      action: "performance_review"

notification_channels:
  - type: "slack"
    webhook: "${SLACK_WEBHOOK_URL}"
    channels: ["#alerts", "#performance"]
  
  - type: "email"
    recipients: ["ops@company.com", "dev@company.com"]
  
  - type: "sms"
    recipients: ["${ONCALL_PHONE}"]
    conditions: ["critical_only"]
```

这个性能测试配置确保了：

1. **全面的性能测试覆盖**：单次、并发、压力、混合负载测试
2. **严格的性能基准**：明确的响应时间和成功率要求
3. **实时监控面板**：系统健康状态和性能趋势监控
4. **自动化告警**：性能异常时及时通知
5. **详细的测试报告**：性能分析和优化建议

通过这套测试体系，可以确保实时功能在生产环境中的稳定性和用户体验。