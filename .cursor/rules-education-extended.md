# education - 扩展规则

## 📋 来源: education-system-standards.md

# 英语四级学习系统开发标准

## 教育系统特殊要求

### 数据安全与隐私保护（单体架构）

- **学生数据保护**：所有学生个人信息必须加密存储，通过统一权限控制系统管理
- **模块间数据传输**：模块间传输学生数据必须通过标准接口，使用 HTTPS 加密
- **数据访问隔离**：用户管理模块负责数据权限控制，其他模块通过接口访问用户数据
- **未成年人保护**：实施使用时长限制（每日 2 小时）、深夜禁用（22:00-6:00）
- **数据脱敏**：测试环境必须使用脱敏数据，禁止使用真实学生信息
- **合规要求**：严格遵循 GDPR、《个人信息保护法》、《网络安全法》
- **应用安全**：所有外部请求必须通过 8000 端口统一入口，实施完整的安全检查

### AI 服务教育适配（单体架构）

- **批改准确性**：AI 模块批改准确率必须>90%（与人工批改对比）
- **教育内容安全**：AI 模块生成内容必须经过教育适宜性检查，不合适内容自动过滤
- **学习效果验证**：AI 分析结果必须可追溯和验证，保存完整调用链路
- **个性化程度**：训练内容与学生薄弱点匹配度>80%
- **模块调用规范**：其他模块调用 AI 模块必须通过标准接口，不得直接访问 AI 模型
- **降级策略**：AI 模块不可用时，训练模块必须提供基础批改功能
- **成本控制**：AI 服务调用必须有配额管理，防止恶意或异常调用

### 业务逻辑标准（跨模块协调）

- **智能训练闭环**：训练模块 →AI 模块分析 → 课程模块调整 → 训练模块优化的完整闭环
- **权限边界**：通过统一认证系统，用户模块控制权限，其他模块验证权限
- **跨模块数据流**：学生数据在用户模块，训练数据在训练模块，通过接口调用获取
- **数据一致性**：关键操作延迟<500ms，跨模块数据同步 24 小时内完成
- **学习路径**：课程模块和训练模块协调支持个性化学习路径
- **模块故障隔离**：单个模块故障不得影响其他教学功能正常运行

### 性能要求

- **并发支持**：1000 学生+500 教师同时在线
- **响应时间**：题目生成<2s，批改<3s，分析<5s
- **可用性**：系统正常运行时间>99.5%
- **数据同步**：实时数据延迟<500ms，批量数据 15 分钟同步

## 代码实现规范

### 教育业务模型

```
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
```

### AI 服务调用标准

```
# AI服务调用必须包含完整的错误处理和监控
async def call_ai_service(prompt: str, service_type: str) -> AIResponse:
    try:
        # 1. 密钥池获取
        api_key = await ai_key_pool.get_best_key()

        # 2. 请求监控
        start_time = time.time()

        # 3. 调用AI服务
```

### 权限控制标准

```
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
- **教学效果测试**：AI 分析准确性和教学调整有效性测试
- **数据安全测试**：权限边界和数据保护测试
- **性能压力测试**：大规模并发用户场景测试

### 业务逻辑测试

```
def test_intelligent_training_loop():
    """测试智能训练闭环完整性"""
    # 1. 学生完成训练
    training_result = student.complete_training(question)

    # 2. AI分析生成报告
    analysis = ai_service.analyze_performance(training_result)

    # 3. 教师收到调整建议
    suggestions = teacher_service.get_adjustment_suggestions(analysis)
```

## 文档要求

### API 文档标准

- 所有教育相关 API 必须包含业务场景说明
- 权限要求必须明确标注
- 数据安全注意事项必须说明
- 性能指标必须量化

### 代码注释标准

```
def generate_adaptive_questions(
    student_id: int,
    training_type: TrainingTypeEnum,
    difficulty_preference: Optional[int] = None
) -> List[Question]:
    """
    为学生生成自适应训练题目

    教育业务逻辑：
    1. 基于学生历史表现分析薄弱知识点
```

这些标准确保智能体开发的代码完全符合教育系统的特殊要求和业务逻辑。
