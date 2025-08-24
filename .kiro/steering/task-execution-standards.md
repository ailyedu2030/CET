---
inclusion: always
---

# 任务执行标准与智能体行为规范

## 核心执行原则

### 1. 任务执行前强制检查清单

```yaml
mandatory_pre_checks:
  architecture_compliance:
    - "验证文件创建位置符合单体架构模块化设计"
    - "确认模块边界清晰，不跨模块混合业务逻辑"
    - "检查模块间接口定义正确"
    - "验证模块间通信通过标准接口而非直接数据库访问"
    
  dependency_validation:
    - "验证所有前置任务已完成并通过验收"
    - "检查依赖的API接口已定义并可用"
    - "确认依赖的数据模型已创建并验证"
    - "验证依赖的基础服务已部署并正常运行"
    - "确认应用健康检查端点正常工作"
    
  environment_readiness:
    - "检查开发环境配置正确"
    - "验证数据库连接可用"
    - "确认AI服务API密钥有效"
    - "检查代码质量工具配置正确"
    - "验证Docker容器编排正常"
    - "确认统一应用服务(8000)端口配置正确"
    
  requirement_clarity:
    - "确认任务需求描述清晰完整"
    - "验证验收标准明确可测试"
    - "确认技术实现方案可行"
    - "检查资源和权限是否充足"
    - "明确任务属于哪个模块的职责范围"
```

### 2. 代码实现强制标准

#### TypeScript/JavaScript 标准
```typescript
// 强制遵循的代码标准
interface CodeStandards {
  // 1. 类型安全 - 零容忍
  strictTypeChecking: true;
  noAnyTypes: true;
  explicitReturnTypes: true;
  
  // 2. 错误处理 - 必须完整
  errorHandlingRequired: true;
  asyncErrorHandling: true;
  userInputValidation: true;
  
  // 3. 性能优化 - 必须考虑
  timeoutForApiCalls: true;
  retryMechanism: true;
  caching: true;
  
  // 4. 安全性 - 必须保证
  inputSanitization: true;
  authenticationCheck: true;
  authorizationValidation: true;
}

// 示例：标准的API调用实现
async function executeAIRequest<T>(
  endpoint: string,
  payload: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);
  
  try {
    // 1. 输入验证
    validatePayload(payload);
    
    // 2. 权限检查
    await validateUserPermissions(options.userId, endpoint);
    
    // 3. API调用
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getValidToken()}`,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    
    // 4. 响应验证
    if (!response.ok) {
      throw new APIError(`Request failed: ${response.status}`, response.status);
    }
    
    const data = await response.json();
    
    // 5. 数据验证
    return validateResponse<T>(data);
    
  } catch (error) {
    // 6. 错误处理和日志
    logger.error('API request failed', {
      endpoint,
      error: error.message,
      userId: options.userId,
    });
    
    if (error.name === 'AbortError') {
      throw new TimeoutError('Request timeout');
    }
    
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}
```

#### Python 标准
```python
# 强制遵循的Python代码标准
from typing import Optional, List, Dict, Any, TypeVar, Generic
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio
from contextlib import asynccontextmanager

T = TypeVar('T')

class ServiceBase(Generic[T]):
    """服务基类 - 强制标准实现模式"""
    
    def __init__(self, db: AsyncSession, logger: logging.Logger) -> None:
        self.db = db
        self.logger = logger
    
    @asynccontextmanager
    async def transaction(self):
        """数据库事务管理 - 强制使用"""
        async with self.db.begin():
            try:
                yield self.db
            except Exception as e:
                await self.db.rollback()
                self.logger.error(f"Transaction failed: {e}")
                raise
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        max_retries: int = 3,
        delay: float = 1.0
    ) -> T:
        """重试机制 - 强制使用"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    self.logger.warning(
                        f"Operation failed, retrying in {delay}s",
                        extra={"attempt": attempt + 1, "error": str(e)}
                    )
                    await asyncio.sleep(delay)
                    delay *= 2  # 指数退避
                else:
                    self.logger.error(
                        f"Operation failed after {max_retries} retries",
                        extra={"error": str(e)}
                    )
        
        raise last_exception

# 示例：标准的服务实现
class TrainingService(ServiceBase[Question]):
    """训练服务 - 遵循所有强制标准"""
    
    async def generate_questions(
        self,
        request: QuestionGenerationRequest,
        user_id: int
    ) -> List[Question]:
        """生成训练题目 - 完整的标准实现"""
        
        # 1. 输入验证
        if not request or not user_id:
            raise ValueError("Invalid input parameters")
        
        # 2. 权限验证
        await self._validate_user_permissions(user_id, "generate_questions")
        
        # 3. 业务逻辑验证
        await self._validate_generation_limits(user_id, request.question_count)
        
        # 4. 数据库事务执行
        async with self.transaction():
            try:
                # 5. AI服务调用（带重试）
                questions_data = await self.execute_with_retry(
                    lambda: self._call_ai_service(request)
                )
                
                # 6. 数据验证和清洗
                validated_questions = self._validate_questions(questions_data)
                
                # 7. 数据库保存
                saved_questions = await self._save_questions(
                    validated_questions, user_id
                )
                
                # 8. 操作日志
                self.logger.info(
                    "Questions generated successfully",
                    extra={
                        "user_id": user_id,
                        "question_count": len(saved_questions),
                        "training_type": request.training_type
                    }
                )
                
                return saved_questions
                
            except Exception as e:
                # 9. 错误处理
                self.logger.error(
                    "Question generation failed",
                    extra={"user_id": user_id, "error": str(e)}
                )
                raise
    
    async def _validate_user_permissions(self, user_id: int, action: str) -> None:
        """权限验证 - 强制实现"""
        # 实现权限检查逻辑
        pass
    
    async def _validate_generation_limits(self, user_id: int, count: int) -> None:
        """业务规则验证 - 强制实现"""
        # 实现业务规则检查
        pass
    
    def _validate_questions(self, questions_data: List[Dict]) -> List[Question]:
        """数据验证 - 强制实现"""
        # 实现数据验证逻辑
        pass
```

### 3. 测试实现强制标准

#### 测试覆盖要求
```yaml
test_requirements:
  coverage_thresholds:
    unit_tests: 80%
    integration_tests: 70%
    e2e_tests: 60%
    critical_paths: 95%
  
  mandatory_test_types:
    - "成功路径测试"
    - "错误处理测试"
    - "边界条件测试"
    - "权限验证测试"
    - "性能基准测试"
  
  test_data_management:
    - "使用工厂模式生成测试数据"
    - "测试数据隔离"
    - "测试后自动清理"
    - "敏感数据脱敏"
```

#### 测试实现模板
```typescript
// 前端测试标准模板
describe('TrainingService', () => {
  let service: TrainingService;
  let mockDependencies: MockDependencies;
  
  beforeEach(() => {
    mockDependencies = createMockDependencies();
    service = new TrainingService(mockDependencies);
  });
  
  afterEach(() => {
    jest.clearAllMocks();
    cleanupTestData();
  });
  
  describe('generateQuestions', () => {
    // 1. 成功路径测试 - 必须
    it('should generate questions successfully with valid input', async () => {
      // Arrange
      const request = createValidRequest();
      const expectedQuestions = createMockQuestions();
      mockDependencies.aiService.generate.mockResolvedValue(expectedQuestions);
      
      // Act
      const result = await service.generateQuestions(request);
      
      // Assert
      expect(result).toEqual(expectedQuestions);
      expect(mockDependencies.aiService.generate).toHaveBeenCalledWith(request);
      expect(mockDependencies.logger.info).toHaveBeenCalled();
    });
    
    // 2. 错误处理测试 - 必须
    it('should handle AI service errors gracefully', async () => {
      // Arrange
      const request = createValidRequest();
      const error = new Error('AI service unavailable');
      mockDependencies.aiService.generate.mockRejectedValue(error);
      
      // Act & Assert
      await expect(service.generateQuestions(request))
        .rejects.toThrow('Failed to generate questions');
      
      expect(mockDependencies.logger.error).toHaveBeenCalledWith(
        expect.stringContaining('AI service error'),
        expect.objectContaining({ error: error.message })
      );
    });
    
    // 3. 边界条件测试 - 必须
    it('should handle empty request gracefully', async () => {
      // Act & Assert
      await expect(service.generateQuestions(null))
        .rejects.toThrow('Invalid request');
    });
    
    // 4. 权限验证测试 - 必须
    it('should validate user permissions', async () => {
      // Arrange
      const request = createValidRequest();
      mockDependencies.authService.checkPermission.mockResolvedValue(false);
      
      // Act & Assert
      await expect(service.generateQuestions(request))
        .rejects.toThrow('Permission denied');
    });
    
    // 5. 性能测试 - 必须
    it('should complete within acceptable time', async () => {
      // Arrange
      const request = createValidRequest();
      const startTime = Date.now();
      
      // Act
      await service.generateQuestions(request);
      
      // Assert
      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(5000); // 5秒内完成
    });
  });
});
```

### 4. 任务完成验收标准

#### 功能完整性检查
```yaml
completion_checklist:
  functionality:
    - "所有需求点已实现"
    - "所有验收标准已满足"
    - "所有边界条件已处理"
    - "所有错误场景已覆盖"
  
  code_quality:
    - "代码通过所有质量检查"
    - "类型检查100%通过"
    - "测试覆盖率达标"
    - "性能基准测试通过"
  
  integration:
    - "与其他模块集成正常"
    - "API接口文档已更新"
    - "数据库迁移脚本正确"
    - "配置文件已更新"
  
  documentation:
    - "代码注释完整"
    - "API文档同步"
    - "README更新"
    - "变更日志记录"
```

#### 自动化验收流程
```bash
#!/bin/bash
# 自动化验收检查脚本

echo "🔍 开始任务完成验收检查..."

# 1. 代码质量检查
echo "📋 代码质量检查..."
npm run lint:check || exit 1
npm run type-check || exit 1
python -m ruff check . || exit 1
python -m mypy . --strict || exit 1

# 2. 测试覆盖率检查
echo "🧪 测试覆盖率检查..."
npm run test:coverage || exit 1
python -m pytest --cov=app --cov-fail-under=80 || exit 1

# 3. 集成测试
echo "🔗 集成测试..."
npm run test:integration || exit 1
python -m pytest tests/integration/ || exit 1

# 4. 性能基准测试
echo "⚡ 性能基准测试..."
npm run test:performance || exit 1

# 5. 安全检查
echo "🔒 安全检查..."
npm audit --audit-level=high || exit 1
python -m bandit -r app/ || exit 1

# 6. 文档同步检查
echo "📚 文档同步检查..."
npm run docs:check || exit 1

echo "✅ 所有验收检查通过！"
```

### 5. 智能体行为监控

#### 实时监控指标
```yaml
monitoring_metrics:
  code_generation:
    - metric: "代码生成成功率"
      threshold: 95%
      alert_threshold: 90%
    
    - metric: "类型错误率"
      threshold: 0%
      alert_threshold: 1%
    
    - metric: "测试通过率"
      threshold: 100%
      alert_threshold: 95%
  
  task_execution:
    - metric: "任务完成率"
      threshold: 95%
      alert_threshold: 90%
    
    - metric: "平均完成时间"
      threshold: "预估时间的120%"
      alert_threshold: "预估时间的150%"
    
    - metric: "返工率"
      threshold: 5%
      alert_threshold: 10%
  
  quality_metrics:
    - metric: "代码重复率"
      threshold: 5%
      alert_threshold: 10%
    
    - metric: "技术债务指数"
      threshold: "A级"
      alert_threshold: "B级"
```

#### 异常处理和自动修正
```typescript
// 智能体异常处理系统
class AgentExceptionHandler {
  private correctionStrategies = new Map<string, CorrectionStrategy>();
  
  constructor() {
    this.setupCorrectionStrategies();
  }
  
  private setupCorrectionStrategies(): void {
    // 类型错误自动修正
    this.correctionStrategies.set('type_error', {
      detect: (error) => error.includes('Type') || error.includes('TS'),
      correct: async (code, error) => {
        return await this.fixTypeErrors(code, error);
      },
      maxAttempts: 3
    });
    
    // 测试失败自动修正
    this.correctionStrategies.set('test_failure', {
      detect: (error) => error.includes('Test failed'),
      correct: async (code, error) => {
        return await this.fixTestFailures(code, error);
      },
      maxAttempts: 2
    });
    
    // 性能问题自动修正
    this.correctionStrategies.set('performance_issue', {
      detect: (error) => error.includes('timeout') || error.includes('slow'),
      correct: async (code, error) => {
        return await this.optimizePerformance(code, error);
      },
      maxAttempts: 1
    });
  }
  
  async handleException(error: string, code: string): Promise<string> {
    for (const [type, strategy] of this.correctionStrategies) {
      if (strategy.detect(error)) {
        let attempts = 0;
        let currentCode = code;
        
        while (attempts < strategy.maxAttempts) {
          try {
            const correctedCode = await strategy.correct(currentCode, error);
            
            // 验证修正结果
            const validationResult = await this.validateCorrection(correctedCode);
            if (validationResult.success) {
              return correctedCode;
            }
            
            currentCode = correctedCode;
            attempts++;
          } catch (correctionError) {
            console.error(`Correction attempt ${attempts + 1} failed:`, correctionError);
            attempts++;
          }
        }
      }
    }
    
    throw new Error(`Unable to automatically correct error: ${error}`);
  }
  
  private async fixTypeErrors(code: string, error: string): Promise<string> {
    // 实现类型错误自动修正逻辑
    // 使用AST分析和TypeScript编译器API
    return code; // 简化实现
  }
  
  private async fixTestFailures(code: string, error: string): Promise<string> {
    // 实现测试失败自动修正逻辑
    // 分析测试失败原因并修正代码
    return code; // 简化实现
  }
  
  private async optimizePerformance(code: string, error: string): Promise<string> {
    // 实现性能优化逻辑
    // 添加缓存、优化算法、减少数据库查询等
    return code; // 简化实现
  }
  
  private async validateCorrection(code: string): Promise<ValidationResult> {
    // 验证修正后的代码是否正确
    return { success: true, errors: [] }; // 简化实现
  }
}
```

### 6. 持续改进机制

#### 学习和优化循环
```yaml
continuous_improvement:
  data_collection:
    - "收集任务执行数据"
    - "分析成功和失败模式"
    - "记录用户反馈"
    - "监控性能指标"
  
  pattern_analysis:
    - "识别高质量代码模式"
    - "分析常见错误类型"
    - "优化代码生成模板"
    - "改进测试策略"
  
  model_optimization:
    - "更新代码生成规则"
    - "优化错误检测算法"
    - "改进自动修正策略"
    - "提升预测准确性"
  
  feedback_loop:
    - "定期评估改进效果"
    - "调整优化策略"
    - "更新最佳实践"
    - "分享成功经验"
```

## 实施路线图

### 第一阶段：基础配置（立即实施）
1. 配置代码质量检查工具
2. 建立测试驱动开发流程
3. 实施任务执行标准

### 第二阶段：监控和自动化（1周内）
1. 部署智能体监控系统
2. 实施自动化验收流程
3. 配置异常处理机制

### 第三阶段：优化和学习（持续）
1. 建立持续改进机制
2. 优化智能体性能
3. 扩展自动修正能力

通过这套完整的任务执行标准，可以确保智能体在每个任务执行过程中都遵循最高的质量标准，实现100%的正确率和成功率。