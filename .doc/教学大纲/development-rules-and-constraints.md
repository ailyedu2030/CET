# 教学大纲和教案生成系统开发规则和约束

## 📋 文档概述

本文档制定了教学大纲和教案生成系统开发过程中必须遵循的规则和约束，确保开发团队按照统一标准，高质量、高效率地完成系统优化开发工作。

## 🏗️ 代码库结构和分离规则

### 前后端代码严格分离

```
✅ 正确的目录结构：
backend/           # 所有Python/Django代码
├── models/       # 数据模型
├── views/        # API视图
├── serializers/  # 序列化器
├── services/     # 业务逻辑
├── utils/        # 工具函数
└── urls.py       # 路由配置

frontend/         # 所有TypeScript/React代码
├── src/app/      # Next.js页面
├── src/components/ # React组件
├── src/lib/      # 前端工具库
├── src/types/    # TypeScript类型
└── src/hooks/    # React Hooks

❌ 绝对禁止：
- 在frontend/目录下创建Python文件
- 在backend/目录下创建React组件
- 混合放置前后端功能代码
```

### 模块化开发规则

```python
# ✅ 正确的模块结构
backend/
├── teaching_syllabus/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── syllabus.py
│   │   └── lesson_plan.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── deepseek_optimizer.py
│   │   └── content_analyzer.py
│   └── views/
│       ├── __init__.py
│       └── syllabus_views.py

# ❌ 禁止的结构
backend/
├── all_models.py      # 所有模型混在一个文件
├── big_service.py     # 所有业务逻辑混在一起
└── views.py           # 所有视图混在一起
```

## 🤖 DeepSeek AI模型使用最佳实践

### 模型选择规则

```python
# ✅ 智能模型选择策略
class ModelSelectionRules:
    SELECTION_MATRIX = {
        "simple_analysis": {
            "model": "deepseek-chat",
            "max_tokens": 4000,
            "temperature": 0.3
        },
        "complex_reasoning": {
            "model": "deepseek-reasoner",
            "max_tokens": 8000,
            "temperature": 0.1
        },
        "creative_generation": {
            "model": "deepseek-chat",
            "max_tokens": 6000,
            "temperature": 0.7
        }
    }

# ❌ 禁止的做法
# 所有任务都使用同一个模型
# 不考虑任务复杂度的参数设置
# 忽略成本优化的模型选择
```

### API调用优化规则

```python
# ✅ 正确的API调用模式
class DeepSeekAPIRules:
    # 1. 必须使用缓存
    @cached_result(ttl=3600)
    async def analyze_content(self, content: str) -> AnalysisResult:
        pass

    # 2. 必须有重试机制
    @retry(max_attempts=3, backoff_factor=2)
    async def call_api(self, request: APIRequest) -> APIResponse:
        pass

    # 3. 必须有错误处理
    try:
        result = await self.deepseek_client.chat(messages)
    except DeepSeekAPIError as e:
        logger.error(f"DeepSeek API error: {e}")
        return self._handle_api_error(e)

# ❌ 禁止的做法
# 直接调用API不使用缓存
# 没有错误处理和重试机制
# 不记录API调用日志和性能指标
```

## 📊 代码质量和测试标准

### 代码质量要求

```python
# ✅ 必须遵循的代码质量标准
class CodeQualityStandards:
    # 1. 类型注解覆盖率 > 95%
    def process_document(
        self,
        document: UploadedDocument,
        config: AnalysisConfig
    ) -> ProcessingResult:
        pass

    # 2. 文档字符串覆盖率 > 90%
    def analyze_content(self, content: str) -> AnalysisResult:
        """
        分析教学内容并提取关键信息

        Args:
            content: 待分析的教学内容文本

        Returns:
            AnalysisResult: 包含分析结果的对象

        Raises:
            ContentAnalysisError: 当内容分析失败时抛出
        """
        pass

    # 3. 单元测试覆盖率 > 85%
    # 4. 集成测试覆盖率 > 70%
```

### 测试规则和标准

```python
# ✅ 测试文件组织结构
tests/
├── unit/
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_workflows.py
└── e2e/
    ├── test_syllabus_generation.py
    └── test_lesson_plan_creation.py

# ✅ 测试命名规则
class TestDeepSeekOptimizer:
    def test_model_selection_for_simple_task(self):
        """测试简单任务的模型选择"""
        pass

    def test_model_selection_for_complex_reasoning(self):
        """测试复杂推理任务的模型选择"""
        pass

    def test_api_error_handling(self):
        """测试API错误处理机制"""
        pass
```

## 🔗 API设计和数据模型一致性规则

### API设计规范

```python
# ✅ RESTful API设计规范
class APIDesignRules:
    # 1. 统一的响应格式
    RESPONSE_FORMAT = {
        "success": bool,
        "data": Any,
        "message": str,
        "error_code": Optional[str],
        "timestamp": datetime
    }

    # 2. 统一的错误处理
    ERROR_CODES = {
        "INVALID_INPUT": "输入参数无效",
        "DEEPSEEK_API_ERROR": "DeepSeek API调用失败",
        "PROCESSING_TIMEOUT": "处理超时",
        "INSUFFICIENT_PERMISSIONS": "权限不足"
    }

    # 3. 统一的分页格式
    PAGINATION_FORMAT = {
        "page": int,
        "page_size": int,
        "total": int,
        "has_next": bool,
        "has_previous": bool
    }
```

### 数据模型一致性规则

```python
# ✅ 前后端数据模型一致性
# Backend Model
class SyllabusModel(UserRelatedModel, StatusTrackingModel):
    title = models.CharField(max_length=200, verbose_name="大纲标题")
    content = models.TextField(verbose_name="大纲内容")
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        verbose_name="难度等级"
    )

# Backend Serializer
class SyllabusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyllabusModel
        fields = ['id', 'title', 'content', 'difficulty_level', 'created_at']

# Frontend TypeScript Type
interface SyllabusData {
  id: number;
  title: string;
  content: string;
  difficulty_level: "easy" | "medium" | "hard";
  created_at: string;
}

# ❌ 禁止的不一致情况
# 后端字段名: difficulty_level, 前端字段名: difficultyLevel
# 后端类型: CharField, 前端类型: number
# 后端有字段但前端没有对应类型定义
```

## ⚠️ 错误处理和性能优化指导原则

### 错误处理规则

```python
# ✅ 分层错误处理策略
class ErrorHandlingRules:
    # 1. 业务逻辑层错误
    class BusinessLogicError(Exception):
        def __init__(self, message: str, error_code: str):
            self.message = message
            self.error_code = error_code
            super().__init__(message)

    # 2. 外部服务错误
    class ExternalServiceError(Exception):
        def __init__(self, service_name: str, original_error: Exception):
            self.service_name = service_name
            self.original_error = original_error
            super().__init__(f"{service_name} service error: {original_error}")

    # 3. 数据验证错误
    class DataValidationError(Exception):
        def __init__(self, field_name: str, validation_message: str):
            self.field_name = field_name
            self.validation_message = validation_message
            super().__init__(f"Validation error for {field_name}: {validation_message}")

# ✅ 错误处理装饰器
def handle_service_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DeepSeekAPIError as e:
            logger.error(f"DeepSeek API error in {func.__name__}: {e}")
            raise ExternalServiceError("DeepSeek", e)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise BusinessLogicError(f"Service error in {func.__name__}", "INTERNAL_ERROR")
    return wrapper
```

### 性能优化规则

```python
# ✅ 性能优化最佳实践
class PerformanceOptimizationRules:
    # 1. 数据库查询优化
    @staticmethod
    def get_syllabi_with_related_data(user_id: int):
        return Syllabus.objects.select_related(
            'user', 'subject'
        ).prefetch_related(
            'lesson_plans', 'assessments'
        ).filter(user_id=user_id)

    # 2. 缓存策略
    @cached_result(ttl=1800)  # 30分钟缓存
    async def analyze_textbook_content(self, content: str) -> AnalysisResult:
        pass

    # 3. 异步处理
    @background_task
    async def generate_lesson_plan_async(self, syllabus_id: int):
        pass

    # 4. 批量处理
    async def process_multiple_documents(self, documents: List[Document]):
        # 批量处理而不是逐个处理
        tasks = [self.process_document(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

## 🔍 代码审查和质量门控

### 代码审查检查清单

```markdown
## 代码审查检查清单

### 功能性检查

- [ ] 功能实现是否符合需求文档
- [ ] 是否有重复功能实现
- [ ] 错误处理是否完整
- [ ] 边界条件是否考虑

### 代码质量检查

- [ ] 类型注解是否完整
- [ ] 文档字符串是否完整
- [ ] 变量和函数命名是否清晰
- [ ] 代码复杂度是否合理

### 性能检查

- [ ] 是否有性能瓶颈
- [ ] 数据库查询是否优化
- [ ] 缓存策略是否合理
- [ ] 内存使用是否优化

### 安全检查

- [ ] 输入验证是否完整
- [ ] 权限控制是否正确
- [ ] 敏感信息是否保护
- [ ] SQL注入防护是否到位

### 测试检查

- [ ] 单元测试是否完整
- [ ] 集成测试是否覆盖
- [ ] 测试用例是否有效
- [ ] 测试覆盖率是否达标
```

### 质量门控标准

```python
# ✅ 质量门控自动化检查
class QualityGateStandards:
    REQUIREMENTS = {
        "code_coverage": {
            "unit_tests": 85,      # 单元测试覆盖率 >= 85%
            "integration_tests": 70 # 集成测试覆盖率 >= 70%
        },
        "code_quality": {
            "type_annotation": 95,  # 类型注解覆盖率 >= 95%
            "docstring": 90,        # 文档字符串覆盖率 >= 90%
            "complexity": 10        # 圈复杂度 <= 10
        },
        "performance": {
            "api_response_time": 3000,  # API响应时间 <= 3秒
            "memory_usage": 512,        # 内存使用 <= 512MB
            "cpu_usage": 80             # CPU使用率 <= 80%
        },
        "security": {
            "vulnerability_scan": "PASS",  # 安全漏洞扫描通过
            "dependency_check": "PASS",    # 依赖安全检查通过
            "code_scan": "PASS"            # 代码安全扫描通过
        }
    }
```

## 📝 完成定义和验收标准

### 任务完成定义

```python
# ✅ 任务完成的标准定义
class TaskCompletionCriteria:
    DEFINITION_OF_DONE = {
        "code_implementation": [
            "功能代码实现完成",
            "单元测试编写完成并通过",
            "集成测试编写完成并通过",
            "代码审查通过",
            "文档更新完成"
        ],
        "quality_assurance": [
            "代码覆盖率达标",
            "性能指标达标",
            "安全检查通过",
            "Linter检查无警告",
            "类型检查通过"
        ],
        "deployment_readiness": [
            "配置文件更新",
            "数据库迁移脚本准备",
            "部署文档更新",
            "回滚方案准备",
            "监控指标配置"
        ]
    }
```

### 验收测试标准

```python
# ✅ 验收测试标准
class AcceptanceTestingStandards:
    TEST_SCENARIOS = {
        "functional_testing": [
            "用户能够成功上传教材文档",
            "系统能够正确分析教材内容",
            "生成的大纲符合质量标准",
            "用户能够编辑和保存大纲",
            "协作功能正常工作"
        ],
        "performance_testing": [
            "单个文档分析时间 < 3分钟",
            "系统支持100并发用户",
            "API响应时间 < 3秒",
            "内存使用稳定在512MB以内",
            "缓存命中率 > 35%"
        ],
        "usability_testing": [
            "用户界面直观易用",
            "工作流程清晰明确",
            "错误信息友好准确",
            "帮助文档完整有效",
            "用户满意度 > 85%"
        ]
    }
```

---

**文档版本**: v1.0  
**创建日期**: 2025-01-22  
**适用范围**: 教学大纲和教案生成系统开发项目  
**强制执行**: 所有开发任务必须严格遵循本规则文档
