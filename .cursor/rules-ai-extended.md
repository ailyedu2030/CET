# ai - 扩展规则

## 📋 来源: deepseek-optimization-guide.md

# DeepSeek API 最佳实践指南

## 🎯 最新模型信息（2025 年 1 月）

### 可用模型

1. **deepseek-chat** (DeepSeek-V3-0324)
   - 上下文长度：64K
   - 输出长度：默认 4K，最大 8K
   - 适用场景：通用对话、内容生成、结构化输出
2. **deepseek-reasoner** (DeepSeek-R1-0528) 🆕
   - 上下文长度：64K
   - 输出长度：默认 32K，最大 64K
   - 适用场景：复杂推理、深度分析、多步骤思考
   - 特殊功能：包含思维链输出

## 💰 最新定价策略

### 标准时段价格（北京时间 08:30-00:30）

| 模型 | 输入（缓存命中）| 输入（缓存未命中）| 输出 |

### 🌙 错峰优惠时段（北京时间 00:30-08:30）

| 模型 | 输入（缓存命中）| 输入（缓存未命中）| 输出 |

## 🚀 智能模型选择策略

### 教育系统场景优化配置

```
class OptimizedDeepSeekConfig:
    """优化的DeepSeek配置"""

    # 模型选择策略
    MODEL_SELECTION = {
        # 复杂分析任务 - 使用推理模型
        "complex_analysis": {
            "model": "deepseek-reasoner",
            "temperature": 1.0,  # 数据分析场景，官方推荐温度
            "max_tokens": 8000,
```

## 🎯 教育场景专用配置

### 1. 智能批改系统配置

```
# 写作批改 - 使用推理模型确保准确性
WRITING_GRADING_CONFIG = {
    "model": "deepseek-reasoner",
    "temperature": 0.5,  # 稍低温度保证评分一致性
    "max_tokens": 4000,
    "system_prompt": """你是专业的英语四级写作评分专家。
请按照四级评分标准进行详细分析和评分。

<think>
在这里进行详细的评分思考过程：
```

### 2. 学情分析系统配置

```
# 深度学情分析 - 使用推理模型
LEARNING_ANALYSIS_CONFIG = {
    "model": "deepseek-reasoner",
    "temperature": 0.6,
    "max_tokens": 6000,
    "system_prompt": """你是教育数据分析专家，请对学生学习数据进行深度分析。

<think>
分析思路：
1. 数据模式识别
```

## ⚡ 性能优化策略

### 1. 智能缓存管理

```
class IntelligentCacheManager:
    """智能缓存管理器"""

    def __init__(self):
        self.cache_strategies = {
            # 高频复用内容 - 长期缓存
            "vocabulary_explanations": {
                "ttl": 86400,  # 24小时
                "cost_savings": 0.75  # 75%成本节省
            },
```

### 2. 错峰调度系统

```
class OffPeakScheduler:
    """错峰调度器"""

    def __init__(self):
        self.off_peak_hours = {
            "start": "00:30",  # 北京时间
            "end": "08:30",
            "timezone": "Asia/Shanghai"
        }

```

## 🔧 API 调用最佳实践

### 1. 标准 API 调用模板

```
async def optimized_deepseek_call(
    messages: List[dict],
    task_type: str,
    priority: str = "normal"
) -> dict:
    """优化的DeepSeek API调用"""

    # 1. 智能模型选择
    config = OptimizedDeepSeekConfig.MODEL_SELECTION.get(
        task_type,
```

### 2. 推理模型专用处理

```
def extract_reasoning_parts(content: str) -> tuple:
    """提取推理模型的思考过程和最终答案"""
    import re

    # 提取思考过程
    think_pattern = r'<think>(.*?)</think>'
    think_match = re.search(think_pattern, content, re.DOTALL)
    thinking = think_match.group(1).strip() if think_match else ""

    # 提取最终答案
```

## 📊 成本控制策略

### 预期成本优化效果

```
COST_OPTIMIZATION_PROJECTION = {
    "current_monthly_cost": 500,  # 假设当前月成本
    "optimizations": {
        "off_peak_scheduling": {
            "savings_ratio": 0.4,  # 40%请求在错峰时段
            "discount": 0.5,       # 5折优惠
            "monthly_savings": 100  # 节省100元
        },
        "intelligent_caching": {
            "cache_hit_rate": 0.3,  # 30%缓存命中率
```

## 🎯 教育系统专用优化

### 1. 批改系统优化

```
# 智能批改配置
GRADING_OPTIMIZATION = {
    "writing_assessment": {
        "model": "deepseek-chat",      # 标准模型，数据分析场景
        "temperature": 1.0,            # 数据分析场景官方推荐温度
        "max_tokens": 4000,
        "cost_per_assessment": "约0.2元"  # 预估成本（使用chat模型更便宜）
    },

    "multiple_choice_grading": {
```

### 2. 个性化学习路径

```
# 学习路径生成配置
LEARNING_PATH_CONFIG = {
    "deep_analysis": {
        "model": "deepseek-reasoner",
        "temperature": 1.0,  # 数据分析场景，深度学情分析
        "max_tokens": 6000,
        "schedule": "off_peak_preferred"  # 优先错峰时段
    },

    "quick_recommendations": {
```

这个配置指南确保 DeepSeek API 在教育系统中的最优使用，平衡了成本、性能和质量。

## 📋 来源: ai-service-temperature-update.md

# AI 服务温度参数更新配置

## 🎯 基于 DeepSeek 官方建议的温度参数调整

根据 DeepSeek 官方文档的温度设置建议，对英语四级学习系统的 AI 服务配置进行全面优化。

## 📊 更新后的 AI 服务配置

### 1. 智能批改系统配置

```
# app/services/ai_grading_service.py
class OptimizedGradingService:
    """优化后的批改服务配置"""

    GRADING_CONFIGS = {
        # 写作批改 - 数据分析场景
        "writing_grading": {
            "model": "deepseek-chat",
            "temperature": 1.0,  # 官方推荐：数据分析场景
            "max_tokens": 3000,
```

### 2. 实时辅助系统配置

```
# app/services/realtime_assist_service.py
class OptimizedRealtimeAssistService:
    """优化后的实时辅助服务配置"""

    ASSIST_CONFIGS = {
        # 写作辅助 - 通用对话场景
        "writing_assist": {
            "model": "deepseek-chat",
            "temperature": 1.3,  # 官方推荐：通用对话场景
            "max_tokens": 300,
```

### 3. 题目生成系统配置

```
# app/services/question_generation_service.py
class OptimizedQuestionGenerationService:
    """优化后的题目生成服务配置"""

    GENERATION_CONFIGS = {
        # 创意题目生成 - 创意写作场景
        "creative_questions": {
            "model": "deepseek-chat",
            "temperature": 1.5,  # 官方推荐：创意类写作场景
            "max_tokens": 4000,
```

### 4. 学情分析系统配置

```
# app/services/learning_analytics_service.py
class OptimizedLearningAnalyticsService:
    """优化后的学情分析服务配置"""

    ANALYTICS_CONFIGS = {
        # 深度学情分析 - 数据分析场景
        "deep_analysis": {
            "model": "deepseek-reasoner",
            "temperature": 1.0,  # 官方推荐：数据分析场景
            "max_tokens": 8000,
```

### 5. 教学内容生成配置

```
# app/services/teaching_content_service.py
class OptimizedTeachingContentService:
    """优化后的教学内容生成服务配置"""

    CONTENT_CONFIGS = {
        # 教学大纲生成 - 创意写作场景
        "syllabus_generation": {
            "model": "deepseek-reasoner",
            "temperature": 1.5,  # 官方推荐：创意类写作场景
            "max_tokens": 6000,
```

## 🔄 配置迁移指南

### 1. 温度参数映射表

| 批改系统 0.3 → 1.0 | 数据分析 | 分析学生作文属于数据分析场景 |
| 实时辅助 0.2 → 1.3 | 通用对话 | 与学生交互属于对话场景 |

### 2. 代码更新步骤

```
# 步骤1：更新配置常量
TEMPERATURE_CONFIGS = {
    "writing_grading": 1.0,      # 数据分析场景
    "realtime_assist": 1.3,      # 通用对话场景
    "listening_subtitle": 1.3,   # 翻译场景
    "question_generation": 1.5,  # 创意写作场景
    "learning_analysis": 1.0,    # 数据分析场景
    "syllabus_generation": 1.5,  # 创意写作场景
    "grammar_check": 0.0,        # 代码生成场景（精确性）
    "vocabulary_explanation": 1.0 # 数据分析场景
```

### 3. 测试验证计划

```
# 温度参数效果验证测试
class TemperatureValidationTest:
    """温度参数效果验证"""

    async def test_grading_consistency(self):
        """测试批改一致性（温度1.0 vs 原0.3）"""
        # 使用相同作文测试不同温度下的批改结果
        pass

    async def test_assist_naturalness(self):
```

## 📈 预期效果

### 1. 批改系统改进

- **准确性提升**：数据分析场景温度 1.0 提供更准确的分析
- **反馈质量**：更好的平衡准确性和灵活性
- **一致性保持**：在准确分析的基础上保持合理一致性

### 2. 实时辅助优化

- **自然度提升**：通用对话场景温度 1.3 提供更自然的交互
- **建议质量**：更符合对话习惯的写作建议
- **用户体验**：更友好的交互体验

### 3. 内容生成增强

- **创造性提升**：创意写作场景温度 1.5 增加内容多样性
- **质量保证**：在创造性基础上保持内容质量
- **教学效果**：更吸引学生的教学内容
  通过这次温度参数优化，英语四级学习系统将更好地发挥 DeepSeek AI 的能力，为用户提供更优质的学习体验。
