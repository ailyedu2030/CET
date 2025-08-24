# 教学大纲生成系统技术实现详细设计

## 📋 文档概述

本文档详细描述了教学大纲生成系统的技术实现方案，包括核心算法实现、服务架构设计、性能优化策略和部署方案。

## 🔧 核心算法实现

### 1. 多轮迭代分析算法

#### 迭代分析引擎核心实现

```python
class IterativeAnalysisEngine:
    """多轮迭代AI分析引擎"""

    def __init__(self):
        self.ai_service = DeepSeekAPIService()
        self.quality_evaluator = AnalysisQualityEvaluator()
        self.context_builder = AnalysisContextBuilder()
        self.termination_detector = TerminationDetector()

    async def start_analysis_session(
        self,
        document: UploadedFile,
        config: AnalysisConfig
    ) -> AnalysisSession:
        """启动多轮分析会话"""

        # 1. 创建分析会话
        session = AnalysisSession.create(
            document=document,
            config=config,
            max_rounds=config.max_rounds,
            quality_threshold=config.quality_threshold
        )

        # 2. 文档预处理
        processed_document = await self._preprocess_document(document)
        session.set_processed_document(processed_document)

        # 3. 第一轮框架分析
        framework_result = await self._analyze_framework(processed_document)
        session.add_round_result(1, framework_result)

        # 4. 迭代分析循环
        while not self.termination_detector.should_terminate(session):
            await self._execute_next_round(session)

        # 5. 最终整合和优化
        final_result = await self._integrate_and_optimize(session)
        session.mark_completed(final_result)

        return session

    async def _execute_next_round(self, session: AnalysisSession):
        """执行下一轮分析"""
        round_number = session.current_round + 1

        # 构建分析上下文
        context = self.context_builder.build_context(session)

        # 确定分析焦点
        focus_strategy = self._determine_focus_strategy(session, context)
        focus_areas = focus_strategy.get_focus_areas()

        # 构建增强提示词
        enhanced_prompt = self._build_enhanced_prompt(
            session.processed_document,
            context,
            focus_areas,
            round_number
        )

        # 执行AI分析
        ai_response = await self.ai_service.generate_response(
            prompt=enhanced_prompt,
            model=self._select_optimal_model(session, round_number),
            temperature=self._calculate_optimal_temperature(session),
            max_tokens=self._calculate_optimal_tokens(session)
        )

        # 解析和验证结果
        parsed_result = self._parse_ai_response(ai_response, round_number)
        validated_result = self._validate_analysis_result(parsed_result, context)

        # 质量评估
        quality_metrics = self.quality_evaluator.evaluate_round(
            session, validated_result
        )
        validated_result.quality_metrics = quality_metrics

        # 添加到会话
        session.add_round_result(round_number, validated_result)

        # 更新上下文
        self.context_builder.update_context(session, validated_result)

    def _determine_focus_strategy(
        self,
        session: AnalysisSession,
        context: AnalysisContext
    ) -> FocusStrategy:
        """确定分析焦点策略"""

        # 分析历史质量趋势
        quality_trend = self._analyze_quality_trend(session)

        # 识别内容缺口
        content_gaps = self._identify_content_gaps(session, context)

        # 评估分析深度
        current_depth = self._evaluate_analysis_depth(session)

        # 选择焦点策略
        if quality_trend.is_improving and content_gaps.has_major_gaps:
            return ContentGapFocusStrategy(content_gaps)
        elif current_depth < context.required_depth:
            return DepthEnhancementStrategy(current_depth, context.required_depth)
        elif quality_trend.is_plateauing:
            return QualityRefinementStrategy(session.latest_result)
        else:
            return BalancedFocusStrategy(session, context)

    def _build_enhanced_prompt(
        self,
        document: ProcessedDocument,
        context: AnalysisContext,
        focus_areas: List[str],
        round_number: int
    ) -> str:
        """构建增强的AI提示词"""

        prompt_builder = EnhancedPromptBuilder()

        # 添加文档内容
        prompt_builder.add_document_content(
            document.content,
            max_length=self._calculate_content_length(round_number)
        )

        # 添加历史上下文
        prompt_builder.add_historical_context(
            context.previous_results,
            context.identified_patterns,
            context.quality_evolution
        )

        # 添加焦点指导
        prompt_builder.add_focus_guidance(
            focus_areas,
            context.analysis_objectives,
            round_number
        )

        # 添加质量要求
        prompt_builder.add_quality_requirements(
            context.quality_standards,
            context.expected_improvements
        )

        # 添加输出格式规范
        prompt_builder.add_output_format(
            self._get_output_schema(round_number),
            context.validation_rules
        )

        return prompt_builder.build()
```

#### 质量评估算法

```python
class AnalysisQualityEvaluator:
    """分析质量评估器"""

    def __init__(self):
        self.metrics_calculators = {
            'completeness': CompletenessCalculator(),
            'accuracy': AccuracyCalculator(),
            'consistency': ConsistencyCalculator(),
            'depth': DepthCalculator(),
            'novelty': NoveltyCalculator()
        }

    def evaluate_round(
        self,
        session: AnalysisSession,
        round_result: RoundResult
    ) -> QualityMetrics:
        """评估单轮分析质量"""

        metrics = {}

        # 计算各维度质量指标
        for metric_name, calculator in self.metrics_calculators.items():
            score = calculator.calculate(session, round_result)
            metrics[metric_name] = score

        # 计算综合质量分数
        overall_score = self._calculate_overall_score(metrics)

        # 计算改进率
        improvement_rate = self._calculate_improvement_rate(session, overall_score)

        # 生成质量报告
        quality_report = self._generate_quality_report(
            metrics, overall_score, improvement_rate
        )

        return QualityMetrics(
            individual_scores=metrics,
            overall_score=overall_score,
            improvement_rate=improvement_rate,
            quality_report=quality_report,
            recommendations=self._generate_recommendations(metrics)
        )

    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """计算综合质量分数"""

        # 权重配置
        weights = {
            'completeness': 0.25,
            'accuracy': 0.30,
            'consistency': 0.20,
            'depth': 0.15,
            'novelty': 0.10
        }

        weighted_sum = sum(
            metrics.get(metric, 0) * weight
            for metric, weight in weights.items()
        )

        return min(weighted_sum, 1.0)

    def _calculate_improvement_rate(
        self,
        session: AnalysisSession,
        current_score: float
    ) -> float:
        """计算相比前轮的改进率"""

        if session.current_round <= 1:
            return 0.0

        previous_result = session.get_round_result(session.current_round - 1)
        if not previous_result:
            return 0.0

        previous_score = previous_result.quality_metrics.overall_score

        if previous_score == 0:
            return 1.0 if current_score > 0 else 0.0

        return (current_score - previous_score) / previous_score

class CompletenessCalculator:
    """完整性计算器"""

    def calculate(self, session: AnalysisSession, round_result: RoundResult) -> float:
        """计算内容完整性分数"""

        # 获取预期内容要素
        expected_elements = self._get_expected_elements(session.document_type)

        # 检查已提取的内容要素
        extracted_elements = self._extract_content_elements(round_result)

        # 计算覆盖率
        coverage_rate = len(extracted_elements & expected_elements) / len(expected_elements)

        # 考虑内容深度
        depth_bonus = self._calculate_depth_bonus(round_result)

        # 考虑内容质量
        quality_factor = self._calculate_quality_factor(round_result)

        return min(coverage_rate + depth_bonus * quality_factor, 1.0)

    def _get_expected_elements(self, document_type: str) -> Set[str]:
        """获取预期的内容要素"""

        element_templates = {
            'syllabus': {
                'course_objectives', 'learning_outcomes', 'content_structure',
                'assessment_methods', 'skill_requirements', 'difficulty_levels',
                'time_allocation', 'prerequisites', 'resources'
            },
            'textbook': {
                'chapter_structure', 'learning_objectives', 'key_concepts',
                'exercises', 'examples', 'difficulty_progression',
                'skill_coverage', 'vocabulary_lists'
            }
        }

        return element_templates.get(document_type, set())
```

### 2. 知识点映射算法

#### 语义相似度计算

```python
class SemanticSimilarityCalculator:
    """语义相似度计算器"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.similarity_cache = SimilarityCache()

    async def calculate_similarity_matrix(
        self,
        syllabus_points: List[KnowledgePoint],
        textbook_points: List[KnowledgePoint]
    ) -> np.ndarray:
        """计算语义相似度矩阵"""

        # 获取嵌入向量
        syllabus_embeddings = await self._get_embeddings(syllabus_points)
        textbook_embeddings = await self._get_embeddings(textbook_points)

        # 计算相似度矩阵
        similarity_matrix = np.zeros((len(syllabus_points), len(textbook_points)))

        for i, s_embedding in enumerate(syllabus_embeddings):
            for j, t_embedding in enumerate(textbook_embeddings):
                # 多种相似度计算方法
                cosine_sim = self._cosine_similarity(s_embedding, t_embedding)
                euclidean_sim = self._euclidean_similarity(s_embedding, t_embedding)
                jaccard_sim = self._jaccard_similarity(
                    syllabus_points[i], textbook_points[j]
                )

                # 加权组合
                combined_sim = (
                    cosine_sim * 0.5 +
                    euclidean_sim * 0.3 +
                    jaccard_sim * 0.2
                )

                similarity_matrix[i][j] = combined_sim

        return similarity_matrix

    async def _get_embeddings(self, knowledge_points: List[KnowledgePoint]) -> List[np.ndarray]:
        """获取知识点的嵌入向量"""

        embeddings = []

        for point in knowledge_points:
            # 检查缓存
            cache_key = self._generate_cache_key(point)
            cached_embedding = self.similarity_cache.get(cache_key)

            if cached_embedding is not None:
                embeddings.append(cached_embedding)
                continue

            # 构建文本表示
            text_representation = self._build_text_representation(point)

            # 获取嵌入向量
            embedding = await self.embedding_service.get_embedding(text_representation)

            # 缓存结果
            self.similarity_cache.set(cache_key, embedding)
            embeddings.append(embedding)

        return embeddings

    def _build_text_representation(self, point: KnowledgePoint) -> str:
        """构建知识点的文本表示"""

        components = [
            point.name,
            point.description,
            ' '.join(point.keywords),
            point.category,
            f"难度:{point.difficulty_level}"
        ]

        # 添加上下文信息
        if point.parent:
            components.append(f"父级:{point.parent.name}")

        if point.children:
            child_names = [child.name for child in point.children]
            components.append(f"子级:{','.join(child_names)}")

        return ' | '.join(filter(None, components))

class OptimalMatchingAlgorithm:
    """最优匹配算法"""

    def find_optimal_matches(
        self,
        similarity_matrix: np.ndarray,
        syllabus_points: List[KnowledgePoint],
        textbook_points: List[KnowledgePoint],
        threshold: float = 0.3
    ) -> List[KnowledgePointMatch]:
        """寻找最优知识点匹配"""

        matches = []

        # 使用匈牙利算法进行最优分配
        row_indices, col_indices = linear_sum_assignment(-similarity_matrix)

        for i, j in zip(row_indices, col_indices):
            similarity_score = similarity_matrix[i][j]

            if similarity_score >= threshold:
                match = KnowledgePointMatch(
                    syllabus_point=syllabus_points[i],
                    textbook_point=textbook_points[j],
                    similarity_score=similarity_score,
                    match_type=self._determine_match_type(similarity_score),
                    confidence=self._calculate_confidence(similarity_score),
                    mapping_rationale=self._generate_rationale(
                        syllabus_points[i], textbook_points[j], similarity_score
                    )
                )
                matches.append(match)

        # 处理未匹配的知识点
        unmatched_syllabus = self._find_unmatched_syllabus_points(
            syllabus_points, matches
        )
        unmatched_textbook = self._find_unmatched_textbook_points(
            textbook_points, matches
        )

        # 尝试多对一和一对多匹配
        additional_matches = self._find_complex_matches(
            unmatched_syllabus, unmatched_textbook, similarity_matrix
        )
        matches.extend(additional_matches)

        return matches

    def _determine_match_type(self, similarity_score: float) -> str:
        """确定匹配类型"""

        if similarity_score >= 0.8:
            return 'exact'
        elif similarity_score >= 0.6:
            return 'strong'
        elif similarity_score >= 0.4:
            return 'moderate'
        else:
            return 'weak'

    def _calculate_confidence(self, similarity_score: float) -> str:
        """计算匹配置信度"""

        if similarity_score >= 0.9:
            return 'very_high'
        elif similarity_score >= 0.7:
            return 'high'
        elif similarity_score >= 0.5:
            return 'medium'
        else:
            return 'low'
```

### 3. 智能课时分配算法

#### 重要性权重计算

```python
class ImportanceWeightCalculator:
    """重要性权重计算器"""

    def __init__(self):
        self.weight_factors = {
            'syllabus_emphasis': 0.4,      # 考纲强调程度
            'exam_frequency': 0.3,         # 考试出现频率
            'difficulty_level': 0.2,       # 难度等级
            'prerequisite_importance': 0.1  # 前置知识重要性
        }

    def calculate_weights(
        self,
        knowledge_hierarchy: KnowledgeHierarchy,
        syllabus_analysis: SyllabusAnalysis
    ) -> Dict[str, float]:
        """计算知识点重要性权重"""

        weights = {}

        for point in knowledge_hierarchy.knowledge_points:
            # 计算各因子分数
            syllabus_score = self._calculate_syllabus_emphasis_score(
                point, syllabus_analysis
            )
            frequency_score = self._calculate_exam_frequency_score(point)
            difficulty_score = self._calculate_difficulty_score(point)
            prerequisite_score = self._calculate_prerequisite_score(
                point, knowledge_hierarchy
            )

            # 加权计算最终权重
            final_weight = (
                syllabus_score * self.weight_factors['syllabus_emphasis'] +
                frequency_score * self.weight_factors['exam_frequency'] +
                difficulty_score * self.weight_factors['difficulty_level'] +
                prerequisite_score * self.weight_factors['prerequisite_importance']
            )

            weights[point.id] = min(max(final_weight, 0.0), 1.0)

        # 归一化权重
        return self._normalize_weights(weights)

    def _calculate_syllabus_emphasis_score(
        self,
        point: KnowledgePoint,
        syllabus_analysis: SyllabusAnalysis
    ) -> float:
        """计算考纲强调程度分数"""

        # 查找在考纲中的提及频率
        mention_count = syllabus_analysis.get_mention_count(point.name)

        # 查找关键词密度
        keyword_density = syllabus_analysis.get_keyword_density(point.keywords)

        # 查找在重要章节中的位置
        section_importance = syllabus_analysis.get_section_importance(point)

        # 综合计算
        emphasis_score = (
            min(mention_count / 10, 1.0) * 0.4 +
            keyword_density * 0.3 +
            section_importance * 0.3
        )

        return emphasis_score

    def _calculate_exam_frequency_score(self, point: KnowledgePoint) -> float:
        """计算考试出现频率分数"""

        # 从历史考试数据中获取出现频率
        historical_frequency = self._get_historical_frequency(point)

        # 从题型分布中获取权重
        question_type_weight = self._get_question_type_weight(point)

        # 从分值分布中获取权重
        score_weight = self._get_score_weight(point)

        frequency_score = (
            historical_frequency * 0.5 +
            question_type_weight * 0.3 +
            score_weight * 0.2
        )

        return frequency_score

class HourAllocationOptimizer:
    """课时分配优化器"""

    def __init__(self):
        self.allocation_strategies = {
            'importance_weighted': ImportanceWeightedStrategy(),
            'difficulty_adjusted': DifficultyAdjustedStrategy(),
            'balanced': BalancedStrategy(),
            'learning_path_optimized': LearningPathOptimizedStrategy()
        }

    def optimize_allocation(
        self,
        knowledge_hierarchy: KnowledgeHierarchy,
        importance_weights: Dict[str, float],
        constraints: AllocationConstraints
    ) -> OptimizedAllocation:
        """优化课时分配"""

        # 1. 基础分配计算
        base_allocation = self._calculate_base_allocation(
            knowledge_hierarchy, importance_weights, constraints
        )

        # 2. 约束条件应用
        constrained_allocation = self._apply_constraints(
            base_allocation, constraints
        )

        # 3. 学习路径优化
        path_optimized_allocation = self._optimize_learning_path(
            constrained_allocation, knowledge_hierarchy
        )

        # 4. 课时模式调整
        mode_adjusted_allocation = self._adjust_hour_modes(
            path_optimized_allocation, constraints.hour_modes
        )

        # 5. 质量评估和微调
        final_allocation = self._fine_tune_allocation(
            mode_adjusted_allocation, knowledge_hierarchy, constraints
        )

        return final_allocation

    def _calculate_base_allocation(
        self,
        knowledge_hierarchy: KnowledgeHierarchy,
        importance_weights: Dict[str, float],
        constraints: AllocationConstraints
    ) -> BaseAllocation:
        """计算基础课时分配"""

        total_hours = constraints.total_hours
        knowledge_points = knowledge_hierarchy.knowledge_points

        # 计算权重总和
        total_weight = sum(importance_weights.values())

        allocations = {}

        for point in knowledge_points:
            # 基于重要性权重的基础分配
            weight_ratio = importance_weights.get(point.id, 0) / total_weight
            base_hours = total_hours * weight_ratio

            # 难度调整
            difficulty_multiplier = self._get_difficulty_multiplier(point.difficulty_level)
            adjusted_hours = base_hours * difficulty_multiplier

            # 最小课时保证
            min_hours = constraints.min_hours_per_point
            final_hours = max(adjusted_hours, min_hours)

            allocations[point.id] = {
                'knowledge_point': point,
                'base_hours': base_hours,
                'difficulty_adjusted_hours': adjusted_hours,
                'final_hours': final_hours,
                'allocation_rationale': self._generate_allocation_rationale(
                    point, weight_ratio, difficulty_multiplier
                )
            }

        return BaseAllocation(allocations)

    def _optimize_learning_path(
        self,
        allocation: ConstrainedAllocation,
        knowledge_hierarchy: KnowledgeHierarchy
    ) -> PathOptimizedAllocation:
        """优化学习路径"""

        # 构建依赖关系图
        dependency_graph = knowledge_hierarchy.dependency_graph

        # 拓扑排序确定学习顺序
        learning_order = self._topological_sort(dependency_graph)

        # 根据依赖关系调整课时分配
        optimized_allocations = {}

        for point_id in learning_order:
            point_allocation = allocation.allocations[point_id]

            # 检查前置知识点的课时分配
            prerequisites = dependency_graph.get_prerequisites(point_id)
            prerequisite_hours = sum(
                optimized_allocations.get(prereq_id, {}).get('final_hours', 0)
                for prereq_id in prerequisites
            )

            # 根据前置知识点调整当前知识点的课时
            if prerequisite_hours > 0:
                # 如果前置知识点课时较多，可以适当减少当前知识点课时
                adjustment_factor = min(1.0, 1.0 - (prerequisite_hours / 20) * 0.1)
                adjusted_hours = point_allocation['final_hours'] * adjustment_factor
            else:
                adjusted_hours = point_allocation['final_hours']

            optimized_allocations[point_id] = {
                **point_allocation,
                'path_optimized_hours': adjusted_hours,
                'learning_order': learning_order.index(point_id)
            }

        return PathOptimizedAllocation(optimized_allocations, learning_order)
```

## 🏗️ 服务架构设计

### 微服务架构

```python
# 服务注册和发现
class ServiceRegistry:
    """服务注册中心"""

    def __init__(self):
        self.services = {}
        self.health_checkers = {}

    def register_service(self, service_name: str, endpoint: str, health_check_url: str):
        """注册服务"""
        self.services[service_name] = {
            'endpoint': endpoint,
            'health_check_url': health_check_url,
            'status': 'healthy',
            'last_check': timezone.now()
        }

    async def get_healthy_endpoint(self, service_name: str) -> Optional[str]:
        """获取健康的服务端点"""
        service_info = self.services.get(service_name)

        if not service_info:
            return None

        # 检查服务健康状态
        if await self._check_service_health(service_name):
            return service_info['endpoint']

        return None

    async def _check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        service_info = self.services[service_name]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    service_info['health_check_url'],
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    is_healthy = response.status == 200

            service_info['status'] = 'healthy' if is_healthy else 'unhealthy'
            service_info['last_check'] = timezone.now()

            return is_healthy

        except Exception:
            service_info['status'] = 'unhealthy'
            service_info['last_check'] = timezone.now()
            return False

# 服务间通信
class ServiceCommunicator:
    """服务间通信管理器"""

    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.circuit_breakers = {}
        self.retry_policies = {}

    async def call_service(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict:
        """调用服务"""

        # 获取服务端点
        base_url = await self.service_registry.get_healthy_endpoint(service_name)
        if not base_url:
            raise ServiceUnavailableError(f"Service {service_name} is not available")

        # 检查熔断器状态
        circuit_breaker = self.circuit_breakers.get(service_name)
        if circuit_breaker and circuit_breaker.is_open():
            raise CircuitBreakerOpenError(f"Circuit breaker is open for {service_name}")

        # 执行请求
        full_url = f"{base_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    full_url,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:

                    if response.status >= 400:
                        raise ServiceError(f"Service error: {response.status}")

                    result = await response.json()

                    # 记录成功调用
                    if circuit_breaker:
                        circuit_breaker.record_success()

                    return result

        except Exception as e:
            # 记录失败调用
            if circuit_breaker:
                circuit_breaker.record_failure()

            # 重试逻辑
            retry_policy = self.retry_policies.get(service_name)
            if retry_policy and retry_policy.should_retry(e):
                await asyncio.sleep(retry_policy.get_delay())
                return await self.call_service(service_name, method, endpoint, data, timeout)

            raise
```

### 异步任务处理

```python
# Celery任务定义
from celery import Celery

app = Celery('teaching_syllabus_system')

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_iterative_analysis(self, session_id: str, config: Dict):
    """异步处理多轮迭代分析"""

    try:
        # 获取分析会话
        session = IterativeAnalysisSession.objects.get(id=session_id)

        # 创建分析引擎
        engine = IterativeAnalysisEngine()

        # 执行分析
        result = asyncio.run(engine.start_analysis_session(session, config))

        # 更新会话状态
        session.mark_completed(result)

        # 发送完成通知
        send_analysis_completion_notification.delay(session_id)

        return {
            'success': True,
            'session_id': session_id,
            'result_summary': result.get_summary()
        }

    except Exception as exc:
        # 记录错误
        logger.error(f"Analysis failed for session {session_id}: {exc}")

        # 更新会话状态
        session = IterativeAnalysisSession.objects.get(id=session_id)
        session.mark_failed(str(exc))

        # 重试逻辑
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            # 发送失败通知
            send_analysis_failure_notification.delay(session_id, str(exc))
            raise

@app.task
def calculate_knowledge_mapping(syllabus_session_id: str, textbook_session_id: str):
    """异步计算知识点映射"""

    try:
        # 获取分析结果
        syllabus_session = IterativeAnalysisSession.objects.get(id=syllabus_session_id)
        textbook_session = IterativeAnalysisSession.objects.get(id=textbook_session_id)

        # 创建映射引擎
        mapping_engine = KnowledgePointMappingEngine()

        # 执行映射计算
        mapping_result = asyncio.run(
            mapping_engine.create_knowledge_mapping(
                syllabus_session.final_result,
                textbook_session.final_result
            )
        )

        # 保存映射结果
        knowledge_hierarchy = KnowledgePointHierarchy.objects.create(
            workflow=syllabus_session.workflow,
            source_analysis_session=syllabus_session,
            hierarchy_type='integrated',
            hierarchy_data=mapping_result.hierarchy,
            importance_weights=mapping_result.weights,
            dependency_graph=mapping_result.dependencies
        )

        # 触发课时分配计算
        calculate_hour_allocation.delay(knowledge_hierarchy.id)

        return {
            'success': True,
            'mapping_id': knowledge_hierarchy.id
        }

    except Exception as exc:
        logger.error(f"Knowledge mapping failed: {exc}")
        raise

@app.task
def calculate_hour_allocation(knowledge_hierarchy_id: str):
    """异步计算课时分配"""

    try:
        # 获取知识点层级
        knowledge_hierarchy = KnowledgePointHierarchy.objects.get(id=knowledge_hierarchy_id)

        # 获取课程配置
        workflow = knowledge_hierarchy.workflow
        course_config = workflow.workflow_config.get('course_config', {})

        # 创建分配引擎
        allocation_engine = SmartHourAllocationEngine()

        # 计算最优分配
        allocation_result = asyncio.run(
            allocation_engine.calculate_optimal_allocation(
                knowledge_hierarchy,
                course_config
            )
        )

        # 保存分配结果
        hour_allocation = CourseHourAllocation.objects.create(
            workflow=workflow,
            knowledge_hierarchy=knowledge_hierarchy,
            allocation_strategy=course_config.get('allocation_strategy', 'importance_weighted'),
            total_hours=course_config.get('total_hours', 48),
            hour_distribution=allocation_result.allocation_data,
            allocation_rationale=allocation_result.rationale,
            allocation_quality_score=allocation_result.quality_score
        )

        # 推进工作流到下一阶段
        advance_workflow_stage.delay(workflow.id)

        return {
            'success': True,
            'allocation_id': hour_allocation.id
        }

    except Exception as exc:
        logger.error(f"Hour allocation failed: {exc}")
        raise
```

## 🚀 DeepSeek模型优化集成

### 优化后的AI分析服务

基于DeepSeek模型特性，我们对AI分析服务进行了全面优化：

```python
class OptimizedAISyllabusAnalyzer:
    """优化的AI考纲分析器"""

    def __init__(self):
        self.deepseek_service = OptimizedDeepSeekService()
        self.prompt_optimizer = DeepSeekPromptOptimizer()

    async def analyze_syllabus_optimized(
        self,
        file: UploadedFile,
        config: AnalysisConfig
    ) -> AnalysisResult:
        """优化的考纲分析"""

        # 1. 文档预处理和长上下文优化
        processed_content = await self._preprocess_for_long_context(file)

        # 2. 第一轮：使用推理模型进行框架分析
        framework_analysis = await self.deepseek_service.analyze_with_reasoning(
            content=processed_content,
            analysis_type="structure_analysis",
            context={"document_type": "syllabus", "analysis_depth": "comprehensive"}
        )

        # 3. 基于框架结果的多轮深度分析
        detailed_analyses = await asyncio.gather(
            self._analyze_knowledge_points_optimized(processed_content, framework_analysis),
            self._analyze_difficulty_levels_optimized(processed_content, framework_analysis),
            self._analyze_skill_requirements_optimized(processed_content, framework_analysis),
            self._assess_teaching_objectives_optimized(processed_content, framework_analysis)
        )

        # 4. 整合分析结果
        integrated_result = await self._integrate_analysis_results(
            framework_analysis,
            detailed_analyses
        )

        return integrated_result

    async def _analyze_knowledge_points_optimized(
        self,
        content: str,
        framework: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化的知识点分析"""

        # 构建基于框架的知识点分析提示词
        analysis_prompt = self.prompt_optimizer.build_reasoning_prompt(
            problem_statement="基于文档框架分析，深度提取和分析知识点",
            analysis_context={
                "document_content": content[:30000],  # 利用长上下文
                "framework_structure": framework.get("reasoning_process", {}),
                "identified_sections": framework.get("final_answer", {}).get("sections", [])
            },
            expected_output="""
            {
                "knowledge_points": [
                    {
                        "id": "kp_001",
                        "name": "知识点名称",
                        "category": "分类",
                        "importance_level": "high/medium/low",
                        "difficulty_level": "beginner/intermediate/advanced",
                        "prerequisites": ["前置知识点"],
                        "learning_objectives": ["学习目标"],
                        "assessment_methods": ["评估方式"]
                    }
                ],
                "knowledge_hierarchy": {...},
                "cross_references": {...}
            }
            """
        )

        return await self.deepseek_service.analyze_with_reasoning(
            content=analysis_prompt,
            analysis_type="knowledge_extraction"
        )
```

### 智能模型选择策略

```python
class IntelligentModelSelector:
    """智能模型选择器"""

    MODEL_SELECTION_MATRIX = {
        ("analysis", "high_complexity"): {
            "model": "deepseek-reasoner",
            "temperature": 0.6,
            "max_tokens": 4000,
            "reasoning_required": True
        },
        ("generation", "structured"): {
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 6000,
            "reasoning_required": False
        },
        ("mapping", "semantic"): {
            "model": "deepseek-reasoner",
            "temperature": 0.5,
            "max_tokens": 3500,
            "reasoning_required": True
        },
        ("allocation", "optimization"): {
            "model": "deepseek-reasoner",
            "temperature": 0.4,
            "max_tokens": 4000,
            "reasoning_required": True
        }
    }

    def select_optimal_configuration(
        self,
        task_type: str,
        complexity: str,
        content_length: int
    ) -> Dict[str, Any]:
        """选择最优配置"""

        # 基础配置选择
        base_config = self.MODEL_SELECTION_MATRIX.get(
            (task_type, complexity),
            self.MODEL_SELECTION_MATRIX[("generation", "structured")]
        )

        # 基于内容长度的动态调整
        if content_length > 50000:  # 长文档
            adjusted_config = base_config.copy()
            adjusted_config["temperature"] = max(0.2, base_config["temperature"] - 0.1)
            adjusted_config["max_tokens"] = min(8000, base_config["max_tokens"] + 1000)
            return adjusted_config

        return base_config
```

### 长上下文优化策略

```python
class LongContextProcessor:
    """长上下文处理器"""

    MAX_CONTEXT_TOKENS = 120000  # DeepSeek-V3的128K上下文限制

    async def optimize_context_usage(
        self,
        primary_content: str,
        supporting_context: Dict[str, Any],
        task_requirements: str
    ) -> str:
        """优化上下文使用"""

        # 1. 计算token使用分配
        allocation = self._calculate_token_allocation(
            len(primary_content),
            len(str(supporting_context)),
            len(task_requirements)
        )

        # 2. 智能内容截取和压缩
        optimized_primary = self._smart_truncate(
            primary_content,
            allocation["primary_tokens"]
        )

        compressed_context = self._compress_supporting_context(
            supporting_context,
            allocation["context_tokens"]
        )

        # 3. 构建最终上下文
        final_context = self._build_optimized_context(
            optimized_primary,
            compressed_context,
            task_requirements
        )

        return final_context

    def _smart_truncate(self, content: str, max_tokens: int) -> str:
        """智能截取内容"""

        if len(content) <= max_tokens:
            return content

        # 分段策略：保留开头、结尾和关键中间段落
        sections = self._identify_key_sections(content)

        # 按重要性排序并选择
        selected_sections = self._select_by_importance(sections, max_tokens)

        return self._reconstruct_content(selected_sections)

    def _identify_key_sections(self, content: str) -> List[Dict[str, Any]]:
        """识别关键段落"""

        # 使用启发式方法识别重要段落
        paragraphs = content.split('\n\n')
        key_sections = []

        for i, paragraph in enumerate(paragraphs):
            importance_score = self._calculate_paragraph_importance(paragraph, i, len(paragraphs))
            key_sections.append({
                "content": paragraph,
                "position": i,
                "importance": importance_score,
                "length": len(paragraph)
            })

        return sorted(key_sections, key=lambda x: x["importance"], reverse=True)
```

### 缓存优化实现

```python
class DeepSeekCacheOptimizer:
    """DeepSeek缓存优化器"""

    def __init__(self):
        self.cache_strategies = {
            "document_analysis": {"ttl": 86400, "compression": True},
            "knowledge_mapping": {"ttl": 43200, "compression": True},
            "hour_allocation": {"ttl": 21600, "compression": False}
        }

    async def get_or_compute_with_cache(
        self,
        operation_type: str,
        input_data: Dict[str, Any],
        compute_function: callable,
        model_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """带缓存的计算"""

        # 1. 生成缓存键
        cache_key = self._generate_intelligent_cache_key(
            operation_type,
            input_data,
            model_config
        )

        # 2. 尝试从缓存获取
        cached_result = await self._get_from_cache(cache_key, operation_type)
        if cached_result:
            return {
                **cached_result,
                "from_cache": True,
                "cache_hit": True,
                "cost_saved": self._calculate_cost_saved(operation_type)
            }

        # 3. 执行计算
        start_time = time.time()
        result = await compute_function()
        computation_time = time.time() - start_time

        # 4. 缓存结果
        await self._store_to_cache(cache_key, result, operation_type)

        return {
            **result,
            "from_cache": False,
            "cache_hit": False,
            "computation_time": computation_time
        }

    def _generate_intelligent_cache_key(
        self,
        operation_type: str,
        input_data: Dict[str, Any],
        model_config: Dict[str, Any]
    ) -> str:
        """生成智能缓存键"""

        # 内容哈希
        content_parts = []
        for key in sorted(input_data.keys()):
            if key.endswith("_content") or key.endswith("_text"):
                # 对长文本内容生成哈希
                content_hash = hashlib.md5(str(input_data[key]).encode()).hexdigest()[:16]
                content_parts.append(f"{key}:{content_hash}")
            else:
                content_parts.append(f"{key}:{input_data[key]}")

        # 模型配置哈希
        model_signature = hashlib.md5(
            json.dumps(model_config, sort_keys=True).encode()
        ).hexdigest()[:8]

        # 组合缓存键
        cache_key = f"deepseek:{operation_type}:{':'.join(content_parts)}:model:{model_signature}"

        return cache_key
```

## 🔗 相关文档

- [DeepSeek优化策略](./deepseek-optimization-strategy.md)
- [DeepSeek实现示例](./deepseek-implementation-examples.md)
- [前端界面设计](./teaching-syllabus-frontend-design.md)
- [实施计划和里程碑](./teaching-syllabus-implementation-plan.md)

---

**文档版本**: v1.1
**创建日期**: 2025-01-22
**最后更新**: 2025-01-22
