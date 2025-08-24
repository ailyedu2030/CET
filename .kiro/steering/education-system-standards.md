---
inclusion: always
---

# 英语四级学习系统开发标准

## 教育系统特殊要求

### 数据安全与隐私保护（单体架构）
- **学生数据保护**：所有学生个人信息必须加密存储，通过统一权限控制系统管理
- **模块间数据传输**：模块间传输学生数据必须通过标准接口，使用HTTPS加密
- **数据访问隔离**：用户管理模块负责数据权限控制，其他模块通过接口访问用户数据
- **未成年人保护**：实施使用时长限制（每日2小时）、深夜禁用（22:00-6:00）
- **数据脱敏**：测试环境必须使用脱敏数据，禁止使用真实学生信息
- **合规要求**：严格遵循GDPR、《个人信息保护法》、《网络安全法》
- **应用安全**：所有外部请求必须通过8000端口统一入口，实施完整的安全检查

### AI服务教育适配（单体架构）
- **批改准确性**：AI模块批改准确率必须>90%（与人工批改对比）
- **教育内容安全**：AI模块生成内容必须经过教育适宜性检查，不合适内容自动过滤
- **学习效果验证**：AI分析结果必须可追溯和验证，保存完整调用链路
- **个性化程度**：训练内容与学生薄弱点匹配度>80%
- **模块调用规范**：其他模块调用AI模块必须通过标准接口，不得直接访问AI模型
- **降级策略**：AI模块不可用时，训练模块必须提供基础批改功能
- **成本控制**：AI服务调用必须有配额管理，防止恶意或异常调用

### 业务逻辑标准（跨模块协调）
- **智能训练闭环**：训练模块→AI模块分析→课程模块调整→训练模块优化的完整闭环
- **权限边界**：通过统一认证系统，用户模块控制权限，其他模块验证权限
- **跨模块数据流**：学生数据在用户模块，训练数据在训练模块，通过接口调用获取
- **数据一致性**：关键操作延迟<500ms，跨模块数据同步24小时内完成
- **学习路径**：课程模块和训练模块协调支持个性化学习路径
- **模块故障隔离**：单个模块故障不得影响其他教学功能正常运行

### 性能要求
- **并发支持**：1000学生+500教师同时在线
- **响应时间**：题目生成<2s，批改<3s，分析<5s
- **可用性**：系统正常运行时间>99.5%
- **数据同步**：实时数据延迟<500ms，批量数据15分钟同步

## 代码实现规范

### 教育业务模型
```python
# 学生训练记录必须包含完整学习轨迹
class TrainingRecord(Base):
    # 必须字段
    student_id: int
    training_type: TrainingTypeEnum
    start_time: datetime
    end_time: datetime
    score: float
    ai_feedback: str
    knowledge_points: List[str]
    
    # 学习分析字段
    difficulty_level: int
    time_spent: int
    error_patterns: Dict
    improvement_suggestions: List[str]
```

### AI服务调用标准
```python
# AI服务调用必须包含完整的错误处理和监控
async def call_ai_service(prompt: str, service_type: str) -> AIResponse:
    try:
        # 1. 密钥池获取
        api_key = await ai_key_pool.get_best_key()
        
        # 2. 请求监控
        start_time = time.time()
        
        # 3. 调用AI服务
        response = await ai_client.generate(prompt, api_key)
        
        # 4. 记录统计
        await ai_key_pool.record_call(api_key, True, time.time() - start_time)
        
        # 5. 教育内容检查
        if not await content_safety_check(response.content):
            raise ContentSafetyError("AI生成内容不适合教育场景")
            
        return response
        
    except Exception as e:
        await ai_key_pool.record_call(api_key, False, time.time() - start_time)
        logger.error(f"AI服务调用失败: {e}")
        raise
```

### 权限控制标准
```python
# 教育系统权限检查必须细粒度控制
async def check_student_data_access(user: User, student_id: int) -> bool:
    if user.user_type == UserType.STUDENT:
        return user.id == student_id
    elif user.user_type == UserType.TEACHER:
        return await is_student_in_teacher_classes(user.id, student_id)
    elif user.user_type == UserType.ADMIN:
        return True
    return False
```

## 测试要求

### 教育场景测试
- **学习流程测试**：完整的学生学习路径端到端测试
- **教学效果测试**：AI分析准确性和教学调整有效性测试
- **数据安全测试**：权限边界和数据保护测试
- **性能压力测试**：大规模并发用户场景测试

### 业务逻辑测试
```python
def test_intelligent_training_loop():
    """测试智能训练闭环完整性"""
    # 1. 学生完成训练
    training_result = student.complete_training(question)
    
    # 2. AI分析生成报告
    analysis = ai_service.analyze_performance(training_result)
    
    # 3. 教师收到调整建议
    suggestions = teacher_service.get_adjustment_suggestions(analysis)
    
    # 4. 系统自动调整训练内容
    adjusted_content = training_service.adjust_content(suggestions)
    
    # 验证闭环完整性
    assert analysis.accuracy > 0.9
    assert len(suggestions) > 0
    assert adjusted_content.difficulty_adjusted
```

## 文档要求

### API文档标准
- 所有教育相关API必须包含业务场景说明
- 权限要求必须明确标注
- 数据安全注意事项必须说明
- 性能指标必须量化

### 代码注释标准
```python
def generate_adaptive_questions(
    student_id: int, 
    training_type: TrainingTypeEnum,
    difficulty_preference: Optional[int] = None
) -> List[Question]:
    """
    为学生生成自适应训练题目
    
    教育业务逻辑：
    1. 基于学生历史表现分析薄弱知识点
    2. 根据遗忘曲线调整复习内容
    3. 结合教师教学进度匹配题目难度
    4. 确保题目符合四级考试标准
    
    Args:
        student_id: 学生ID，用于获取个人学习数据
        training_type: 训练类型（词汇/听力/阅读/写作/翻译）
        difficulty_preference: 难度偏好，None时使用自适应算法
        
    Returns:
        个性化题目列表，按难度梯度排序
        
    Raises:
        PermissionError: 无权限访问学生数据
        AIServiceError: AI服务调用失败
        ContentSafetyError: 生成内容不符合教育标准
        
    Performance:
        - 响应时间: <2秒
        - 个性化匹配度: >80%
        - 题目质量评分: >85%
    """
```

这些标准确保智能体开发的代码完全符合教育系统的特殊要求和业务逻辑。