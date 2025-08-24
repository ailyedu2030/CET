---
inclusion: always
---

# DeepSeek API 最佳实践指南

## 🎯 最新模型信息（2025年1月）

### 可用模型
1. **deepseek-chat** (DeepSeek-V3-0324)
   - 上下文长度：64K
   - 输出长度：默认4K，最大8K
   - 适用场景：通用对话、内容生成、结构化输出

2. **deepseek-reasoner** (DeepSeek-R1-0528) 🆕
   - 上下文长度：64K
   - 输出长度：默认32K，最大64K
   - 适用场景：复杂推理、深度分析、多步骤思考
   - 特殊功能：包含思维链输出

## 💰 最新定价策略

### 标准时段价格（北京时间 08:30-00:30）
| 模型 | 输入（缓存命中）| 输入（缓存未命中）| 输出 |
|------|----------------|------------------|------|
| deepseek-chat | 0.5元/百万tokens | 2元/百万tokens | 8元/百万tokens |
| deepseek-reasoner | 1元/百万tokens | 4元/百万tokens | 16元/百万tokens |

### 🌙 错峰优惠时段（北京时间 00:30-08:30）
| 模型 | 输入（缓存命中）| 输入（缓存未命中）| 输出 |
|------|----------------|------------------|------|
| deepseek-chat | 0.25元（5折）| 1元（5折）| 4元（5折）|
| deepseek-reasoner | 0.25元（2.5折）| 1元（2.5折）| 4元（2.5折）|

## 🚀 智能模型选择策略

### 教育系统场景优化配置

```python
class OptimizedDeepSeekConfig:
    """优化的DeepSeek配置"""
    
    # 模型选择策略
    MODEL_SELECTION = {
        # 复杂分析任务 - 使用推理模型
        "complex_analysis": {
            "model": "deepseek-reasoner",
            "temperature": 1.0,  # 数据分析场景，官方推荐温度
            "max_tokens": 8000,
            "top_p": 0.9,
            "use_cases": [
                "学情深度分析",
                "教学策略推理", 
                "复杂题目生成",
                "多维度评估"
            ]
        },
        
        # 结构化生成 - 使用标准模型分析温度
        "structured_generation": {
            "model": "deepseek-chat",
            "temperature": 1.0,  # 数据分析场景，官方推荐温度
            "max_tokens": 4000,
            "top_p": 0.8,
            "use_cases": [
                "JSON格式输出",
                "标准化批改",
                "数据提取",
                "格式转换"
            ]
        },
        
        # 创意生成 - 使用标准模型创意温度
        "creative_generation": {
            "model": "deepseek-chat", 
            "temperature": 1.5,  # 创意类写作场景，官方推荐温度
            "max_tokens": 6000,
            "top_p": 0.95,
            "use_cases": [
                "题目创意生成",
                "教案内容创作",
                "学习建议生成",
                "反馈文本生成"
            ]
        }
    }
    
    # 成本优化策略
    COST_OPTIMIZATION = {
        "peak_hours_avoidance": {
            "enabled": True,
            "off_peak_start": "00:30",  # 北京时间
            "off_peak_end": "08:30",
            "cost_savings": {
                "deepseek-chat": 0.5,      # 5折
                "deepseek-reasoner": 0.25   # 2.5折
            }
        },
        
        "caching_strategy": {
            "enabled": True,
            "cache_hit_cost_ratio": 0.25,  # 缓存命中仅25%成本
            "cache_ttl": {
                "question_generation": 3600,    # 1小时
                "content_analysis": 7200,       # 2小时  
                "student_assessment": 1800      # 30分钟
            }
        }
    }
```

## 🎯 教育场景专用配置

### 1. 智能批改系统配置

```python
# 写作批改 - 使用推理模型确保准确性
WRITING_GRADING_CONFIG = {
    "model": "deepseek-reasoner",
    "temperature": 0.5,  # 稍低温度保证评分一致性
    "max_tokens": 4000,
    "system_prompt": """你是专业的英语四级写作评分专家。
请按照四级评分标准进行详细分析和评分。

<think>
在这里进行详细的评分思考过程：
1. 内容分析（是否切题、观点是否明确）
2. 语言质量（语法、词汇、句式）
3. 组织结构（逻辑性、连贯性）
4. 格式规范（字数、格式要求）
</think>

<answer>
提供最终评分和详细反馈
</answer>"""
}

# 题目生成 - 使用标准模型平衡创意和质量
QUESTION_GENERATION_CONFIG = {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 3000,
    "response_format": {"type": "json_object"}  # 结构化输出
}
```

### 2. 学情分析系统配置

```python
# 深度学情分析 - 使用推理模型
LEARNING_ANALYSIS_CONFIG = {
    "model": "deepseek-reasoner", 
    "temperature": 0.6,
    "max_tokens": 6000,
    "system_prompt": """你是教育数据分析专家，请对学生学习数据进行深度分析。

<think>
分析思路：
1. 数据模式识别
2. 学习趋势分析  
3. 薄弱环节诊断
4. 改进策略推理
</think>

<answer>
提供具体的分析结论和建议
</answer>"""
}
```

## ⚡ 性能优化策略

### 1. 智能缓存管理

```python
class IntelligentCacheManager:
    """智能缓存管理器"""
    
    def __init__(self):
        self.cache_strategies = {
            # 高频复用内容 - 长期缓存
            "vocabulary_explanations": {
                "ttl": 86400,  # 24小时
                "cost_savings": 0.75  # 75%成本节省
            },
            
            # 学生分析 - 中期缓存  
            "student_analysis": {
                "ttl": 3600,   # 1小时
                "cost_savings": 0.75
            },
            
            # 题目生成 - 短期缓存
            "question_generation": {
                "ttl": 1800,   # 30分钟
                "cost_savings": 0.75
            }
        }
    
    def generate_cache_key(self, content: str, model_config: dict) -> str:
        """生成智能缓存键"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        config_hash = hashlib.md5(str(sorted(model_config.items())).encode()).hexdigest()[:8]
        return f"deepseek:{content_hash}:{config_hash}"
```

### 2. 错峰调度系统

```python
class OffPeakScheduler:
    """错峰调度器"""
    
    def __init__(self):
        self.off_peak_hours = {
            "start": "00:30",  # 北京时间
            "end": "08:30",
            "timezone": "Asia/Shanghai"
        }
    
    def is_off_peak_time(self) -> bool:
        """判断是否为错峰时段"""
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        current_time = now.time()
        
        off_peak_start = time(0, 30)  # 00:30
        off_peak_end = time(8, 30)    # 08:30
        
        return off_peak_start <= current_time <= off_peak_end
    
    async def schedule_api_call(self, api_call_func, priority: str = "normal"):
        """智能调度API调用"""
        if priority == "urgent":
            # 紧急任务立即执行
            return await api_call_func()
        
        elif priority == "cost_sensitive" and not self.is_off_peak_time():
            # 成本敏感任务延迟到错峰时段
            delay_seconds = self._calculate_delay_to_off_peak()
            await asyncio.sleep(delay_seconds)
        
        return await api_call_func()
```

## 🔧 API调用最佳实践

### 1. 标准API调用模板

```python
async def optimized_deepseek_call(
    messages: List[dict],
    task_type: str,
    priority: str = "normal"
) -> dict:
    """优化的DeepSeek API调用"""
    
    # 1. 智能模型选择
    config = OptimizedDeepSeekConfig.MODEL_SELECTION.get(
        task_type, 
        OptimizedDeepSeekConfig.MODEL_SELECTION["structured_generation"]
    )
    
    # 2. 缓存检查
    cache_key = cache_manager.generate_cache_key(
        str(messages), config
    )
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        return cached_result
    
    # 3. 错峰调度
    result = await off_peak_scheduler.schedule_api_call(
        lambda: _call_deepseek_api(messages, config),
        priority
    )
    
    # 4. 结果缓存
    await cache_manager.set(cache_key, result, ttl=3600)
    
    return result

async def _call_deepseek_api(messages: List[dict], config: dict) -> dict:
    """实际的API调用"""
    try:
        response = await openai_client.chat.completions.create(
            model=config["model"],
            messages=messages,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            top_p=config.get("top_p", 1.0),
            stream=False
        )
        
        # 处理推理模型的特殊输出
        if config["model"] == "deepseek-reasoner":
            content = response.choices[0].message.content
            thinking, answer = extract_reasoning_parts(content)
            return {
                "thinking": thinking,
                "answer": answer,
                "usage": response.usage.dict(),
                "model": config["model"]
            }
        else:
            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.dict(),
                "model": config["model"]
            }
            
    except Exception as e:
        logger.error(f"DeepSeek API调用失败: {e}")
        raise
```

### 2. 推理模型专用处理

```python
def extract_reasoning_parts(content: str) -> tuple:
    """提取推理模型的思考过程和最终答案"""
    import re
    
    # 提取思考过程
    think_pattern = r'<think>(.*?)</think>'
    think_match = re.search(think_pattern, content, re.DOTALL)
    thinking = think_match.group(1).strip() if think_match else ""
    
    # 提取最终答案
    answer_pattern = r'<answer>(.*?)</answer>'
    answer_match = re.search(answer_pattern, content, re.DOTALL)
    answer = answer_match.group(1).strip() if answer_match else content
    
    return thinking, answer
```

## 📊 成本控制策略

### 预期成本优化效果

```python
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
            "cost_reduction": 0.75, # 75%成本降低
            "monthly_savings": 75   # 节省75元
        },
        "model_optimization": {
            "reasoner_usage_optimization": 0.2,  # 20%使用推理模型
            "chat_model_efficiency": 0.15,      # 15%效率提升
            "monthly_savings": 50               # 节省50元
        }
    },
    "total_monthly_savings": 225,  # 总计节省225元
    "optimized_monthly_cost": 275, # 优化后成本275元
    "cost_reduction_ratio": 0.45   # 45%成本降低
}
```

## 🎯 教育系统专用优化

### 1. 批改系统优化

```python
# 智能批改配置
GRADING_OPTIMIZATION = {
    "writing_assessment": {
        "model": "deepseek-chat",      # 标准模型，数据分析场景
        "temperature": 1.0,            # 数据分析场景官方推荐温度
        "max_tokens": 4000,
        "cost_per_assessment": "约0.2元"  # 预估成本（使用chat模型更便宜）
    },
    
    "multiple_choice_grading": {
        "model": "deepseek-chat",      # 标准模型足够
        "temperature": 0.0,            # 代码生成场景，需要精确性
        "max_tokens": 1000,
        "cost_per_assessment": "约0.03元"
    }
}
```

### 2. 个性化学习路径

```python
# 学习路径生成配置
LEARNING_PATH_CONFIG = {
    "deep_analysis": {
        "model": "deepseek-reasoner",
        "temperature": 1.0,  # 数据分析场景，深度学情分析
        "max_tokens": 6000,
        "schedule": "off_peak_preferred"  # 优先错峰时段
    },
    
    "quick_recommendations": {
        "model": "deepseek-chat", 
        "temperature": 1.3,  # 通用对话场景，提供学习建议
        "max_tokens": 2000,
        "cache_ttl": 1800  # 30分钟缓存
    }
}
```

这个配置指南确保DeepSeek API在教育系统中的最优使用，平衡了成本、性能和质量。