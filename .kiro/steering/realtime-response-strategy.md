---
inclusion: always
---

# 实时响应策略配置指南

## 🎯 实时性需求分析

基于项目需求文档分析，系统功能按实时性要求分为三个等级：

### 🚨 极高实时性（<3 秒，必须立即响应）

#### 1. 智能批改与反馈系统

- **功能**：学生完成训练后的即时批改
- **要求**：批改响应时间<3 秒，反馈详细度>85%
- **用户体验**：学生做完作业立即看到结果和解析
- **配置策略**：使用流式输出，实时显示批改进度

#### 2. 训练系统实时辅助

- **功能**：写作训练中的语法检查、词汇建议、句式优化
- **要求**：实时响应用户输入
- **用户体验**：打字时即时提示和纠错
- **配置策略**：使用流式输出，边输入边提示

#### 3. 听力训练实时功能

- **功能**：实时字幕、跟读练习反馈
- **要求**：音频播放同步显示
- **用户体验**：无延迟的听力辅助
- **配置策略**：使用流式输出，同步音频进度

### ⚡ 高实时性（<5 秒，快速响应）

#### 1. 题目生成

- **功能**：教师配置参数后生成训练题目
- **要求**：题目生成<2 秒
- **用户体验**：快速获得训练内容
- **配置策略**：非流式输出，但高优先级处理

#### 2. 学情查询和状态更新

- **功能**：实时查询学生学习状态、注册状态
- **要求**：查询响应<1 秒
- **用户体验**：即时获取状态信息
- **配置策略**：缓存+实时更新机制

#### 3. 系统监控和告警

- **功能**：实时监控系统状态、安全事件
- **要求**：异常检测<5 秒内告警
- **用户体验**：及时发现和处理问题
- **配置策略**：实时数据流处理

### 🕐 中等实时性（可错峰处理）

#### 1. 深度学情分析

- **功能**：AI 分析学生学习数据，生成详细报告
- **要求**：分析<5 秒，但可延迟处理
- **用户体验**：详细分析结果，不要求即时
- **配置策略**：错峰调度，使用推理模型

#### 2. 教学大纲和教案生成

- **功能**：基于教材和考纲生成教学内容
- **要求**：质量优先，时间可接受
- **用户体验**：高质量内容生成
- **配置策略**：错峰调度，深度推理

#### 3. 数据统计和报表生成

- **功能**：生成各类统计报表和分析报告
- **要求**：准确性优先
- **用户体验**：定期获取详细报告
- **配置策略**：批量处理，错峰执行

## 🔧 技术实现策略

### 流式输出配置

```python
class StreamingResponseConfig:
    """流式输出配置"""

    # 极高实时性场景 - 使用流式输出
    STREAMING_SCENARIOS = {
        "writing_grading": {
            "model": "deepseek-chat",  # 标准模型足够快
            "temperature": 1.0,        # 数据分析场景，使用官方推荐温度
            "max_tokens": 2000,
            "stream": True,  # 启用流式输出
            "priority": "urgent",
            "timeout": 10,  # 10秒超时
            "chunk_callback": "display_grading_progress"
        },

        "realtime_writing_assist": {
            "model": "deepseek-chat",
            "temperature": 1.3,  # 通用对话场景，提供写作建议
            "max_tokens": 500,   # 短回复
            "stream": True,
            "priority": "urgent",
            "timeout": 5,
            "chunk_callback": "display_suggestions"
        },

        "listening_realtime_subtitle": {
            "model": "deepseek-chat",
            "temperature": 1.3,  # 翻译场景，音频转文字
            "max_tokens": 200,
            "stream": True,
            "priority": "urgent",
            "timeout": 3,
            "chunk_callback": "display_subtitle"
        }
    }

    # 高实时性场景 - 非流式但高优先级
    HIGH_PRIORITY_SCENARIOS = {
        "question_generation": {
            "model": "deepseek-chat",
            "temperature": 1.5,  # 创意类写作场景，生成多样化题目
            "max_tokens": 3000,
            "stream": False,  # 非流式，一次性返回
            "priority": "high",
            "timeout": 8,
            "cache_enabled": True
        },

        "quick_analysis": {
            "model": "deepseek-chat",
            "temperature": 1.0,  # 数据分析场景，官方推荐温度
            "max_tokens": 1500,
            "stream": False,
            "priority": "high",
            "timeout": 6,
            "cache_enabled": True
        }
    }

    # 可错峰处理场景 - 使用推理模型
    OFF_PEAK_SCENARIOS = {
        "deep_learning_analysis": {
            "model": "deepseek-reasoner",  # 推理模型
            "temperature": 1.0,  # 数据分析场景，深度学情分析
            "max_tokens": 8000,
            "stream": False,
            "priority": "cost_sensitive",  # 成本敏感
            "timeout": 30,
            "schedule": "off_peak_preferred"
        },

        "syllabus_generation": {
            "model": "deepseek-reasoner",
            "temperature": 1.5,  # 创意类写作场景，生成教学大纲
            "max_tokens": 6000,
            "stream": False,
            "priority": "cost_sensitive",
            "timeout": 25,
            "schedule": "off_peak_preferred"
        }
    }

class RealtimeResponseService:
    """实时响应服务"""

    def __init__(self):
        self.streaming_config = StreamingResponseConfig()
        self.response_cache = ResponseCache()
        self.priority_queue = PriorityQueue()

    async def handle_streaming_request(
        self,
        scenario: str,
        messages: List[Dict],
        callback_func: Callable = None
    ) -> AsyncGenerator[str, None]:
        """处理流式请求"""

        config = self.streaming_config.STREAMING_SCENARIOS.get(scenario)
        if not config:
            raise ValueError(f"未知的流式场景: {scenario}")

        # 检查缓存
        cache_key = self._generate_cache_key(messages, config)
        cached_response = await self.response_cache.get_streaming(cache_key)
        if cached_response:
            async for chunk in cached_response:
                yield chunk
            return

        # 流式API调用
        response_chunks = []
        async for chunk in self._stream_api_call(messages, config):
            response_chunks.append(chunk)

            # 实时回调处理
            if callback_func:
                await callback_func(chunk)

            yield chunk

        # 缓存完整响应
        await self.response_cache.set_streaming(
            cache_key, response_chunks, ttl=1800
        )

    async def _stream_api_call(
        self,
        messages: List[Dict],
        config: Dict
    ) -> AsyncGenerator[str, None]:
        """执行流式API调用"""

        try:
            # 获取最佳API密钥
            api_key = await self.key_pool.get_best_key_urgent()

            # 流式调用DeepSeek API
            async with openai.AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            ) as client:

                stream = await client.chat.completions.create(
                    model=config["model"],
                    messages=messages,
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    stream=True,  # 启用流式输出
                    timeout=config["timeout"]
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield content

        except Exception as e:
            logger.error(f"流式API调用失败: {e}")
            # 降级到缓存结果
            fallback_response = await self._get_fallback_response(messages)
            yield fallback_response

class PriorityBasedScheduler:
    """基于优先级的调度器"""

    def __init__(self):
        self.urgent_queue = asyncio.Queue(maxsize=100)
        self.high_queue = asyncio.Queue(maxsize=500)
        self.normal_queue = asyncio.Queue(maxsize=1000)
        self.cost_sensitive_queue = asyncio.Queue(maxsize=2000)

    async def schedule_request(self, request: Dict, priority: str):
        """根据优先级调度请求"""

        if priority == "urgent":
            # 紧急请求 - 立即处理
            await self.urgent_queue.put(request)
            return await self._process_urgent_request(request)

        elif priority == "high":
            # 高优先级 - 快速处理
            await self.high_queue.put(request)
            return await self._process_high_priority_request(request)

        elif priority == "cost_sensitive":
            # 成本敏感 - 错峰处理
            if self.off_peak_scheduler.is_off_peak_time():
                return await self._process_request_immediately(request)
            else:
                await self.cost_sensitive_queue.put(request)
                return await self._schedule_for_off_peak(request)

        else:
            # 普通请求
            await self.normal_queue.put(request)
            return await self._process_normal_request(request)

    async def _process_urgent_request(self, request: Dict):
        """处理紧急请求 - 最高优先级"""
        # 跳过所有队列，立即处理
        return await self._execute_api_call(request, bypass_queue=True)

    async def _schedule_for_off_peak(self, request: Dict):
        """调度到错峰时段"""
        delay_seconds = self.off_peak_scheduler.calculate_delay_to_off_peak()

        if delay_seconds > 3600:  # 超过1小时则立即处理
            return await self._execute_api_call(request)

        # 延迟到错峰时段
        await asyncio.sleep(delay_seconds)
        return await self._execute_api_call(request)
```

## 📊 实时批改系统配置

### 流式批改实现

```python
class RealtimeGradingService:
    """实时批改服务 - 专门处理学生作业的即时批改"""

    def __init__(self):
        self.deepseek_service = OptimizedDeepSeekService()
        self.grading_cache = GradingCache()
        self.performance_monitor = RealtimePerformanceMonitor()

    async def stream_writing_grading(
        self,
        student_id: int,
        writing_content: str,
        question_type: str
    ) -> AsyncGenerator[Dict, None]:
        """流式写作批改 - 学生提交后立即开始批改"""

        start_time = time.time()

        try:
            # 1. 发送开始信号
            yield {
                "type": "start",
                "message": "开始批改您的作文...",
                "progress": 0
            }

            # 2. 构建批改提示词
            grading_messages = self._build_grading_messages(
                writing_content, question_type
            )

            # 3. 流式批改
            accumulated_content = ""
            progress = 10

            async for chunk in self.deepseek_service.intelligent_api_call(
                messages=grading_messages,
                task_type="writing_grading",
                priority="urgent",
                stream=True
            ):
                accumulated_content += chunk
                progress = min(90, progress + 2)

                # 实时返回批改进度
                yield {
                    "type": "progress",
                    "content": chunk,
                    "accumulated": accumulated_content,
                    "progress": progress
                }

            # 4. 解析批改结果
            grading_result = self._parse_grading_result(accumulated_content)

            # 5. 保存批改记录
            await self._save_grading_record(
                student_id, writing_content, grading_result
            )

            # 6. 发送完成信号
            response_time = time.time() - start_time
            await self.performance_monitor.record_grading_time(
                "writing_grading", response_time
            )

            yield {
                "type": "complete",
                "result": grading_result,
                "progress": 100,
                "response_time": response_time
            }

        except Exception as e:
            logger.error(f"流式批改失败: {e}")

            # 降级到缓存结果
            fallback_result = await self._get_fallback_grading(
                writing_content, question_type
            )

            yield {
                "type": "error",
                "message": "批改服务暂时不可用，已为您提供参考评分",
                "fallback_result": fallback_result
            }

    def _build_grading_messages(self, content: str, question_type: str) -> List[Dict]:
        """构建批改提示词"""

        system_prompt = f"""
你是专业的英语四级写作评分专家。请按照四级评分标准对以下{question_type}进行详细批改。

评分维度：
1. 内容完整性（25%）- 是否切题，观点是否明确
2. 语言准确性（35%）- 语法、词汇、句式的正确性
3. 组织结构（25%）- 逻辑性、连贯性、段落结构
4. 语言丰富性（15%）- 词汇多样性、句式变化

请提供：
- 总体评分（满分15分）
- 各维度详细分析
- 具体修改建议
- 优秀表达和问题表达的对比
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请批改以下作文：\\n\\n{content}"}
        ]

    async def stream_realtime_writing_assist(
        self,
        current_text: str,
        cursor_position: int
    ) -> AsyncGenerator[Dict, None]:
        """实时写作辅助 - 边写边提示"""

        # 只对最后一句话进行分析，减少计算量
        last_sentence = self._extract_last_sentence(current_text, cursor_position)

        if len(last_sentence) < 10:  # 太短不分析
            return

        assist_messages = [
            {
                "role": "system",
                "content": "你是英语写作助手。请对用户正在写的句子提供简短的语法检查和改进建议。回复要简洁，不超过50字。"
            },
            {
                "role": "user",
                "content": f"请检查这个句子：{last_sentence}"
            }
        ]

        try:
            async for chunk in self.deepseek_service.intelligent_api_call(
                messages=assist_messages,
                task_type="realtime_assist",
                priority="urgent",
                stream=True
            ):
                yield {
                    "type": "suggestion",
                    "content": chunk,
                    "position": cursor_position
                }

        except Exception as e:
            logger.error(f"实时辅助失败: {e}")
            yield {
                "type": "error",
                "message": "写作辅助暂时不可用"
            }
```

## 📋 配置总结

### 实时性配置矩阵

| 功能场景 | 响应要求 | 输出方式 | 模型选择          | 温度设置 | 应用场景 | 优先级         | 错峰调度 |
| -------- | -------- | -------- | ----------------- | -------- | -------- | -------------- | -------- |
| 智能批改 | <3 秒    | 流式     | deepseek-chat     | 1.0      | 数据分析 | urgent         | 否       |
| 实时辅助 | <1 秒    | 流式     | deepseek-chat     | 1.3      | 通用对话 | urgent         | 否       |
| 听力字幕 | <1 秒    | 流式     | deepseek-chat     | 1.3      | 翻译场景 | urgent         | 否       |
| 题目生成 | <2 秒    | 非流式   | deepseek-chat     | 1.5      | 创意写作 | high           | 否       |
| 快速分析 | <5 秒    | 非流式   | deepseek-chat     | 1.0      | 数据分析 | high           | 否       |
| 学情分析 | <5 秒    | 非流式   | deepseek-reasoner | 1.0      | 数据分析 | normal         | 是       |
| 大纲生成 | 可延迟   | 非流式   | deepseek-reasoner | 1.5      | 创意写作 | cost_sensitive | 是       |

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

这个配置确保了关键的用户交互功能（如批改、实时辅助）获得最佳响应速度，同时通过错峰调度优化了非关键功能的成本。
