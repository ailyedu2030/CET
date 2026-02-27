# CET剩余高优先级问题详细修复计划

> 日期: 2026-02-27
> 前置工作: 已完成5个CRITICAL问题修复
> 待修复: 5个HIGH优先级问题

---

## 一、问题清单

| # | 问题 | 优先级 | 预估复杂度 |
|---|------|---------|-----------|
| 1 | 课程: 实现StudentCourse注册记录 | HIGH | 高 |
| 2 | 课程: 持久化CourseAssignment分配 | HIGH | 中 |
| 3 | AI批改: 实现缓存逻辑(stub) | HIGH | 中 |
| 4 | AI批改: 实现评分历史(stub) | HIGH | 中 |
| 5 | 通知: 添加清理Celery任务 | HIGH | 低 |
| 6 | 权限: 实现is_public参数(资源上传) | CRITICAL | 低 |

---

## 二、问题2: 持久化CourseAssignment分配

### 当前问题分析

**文件**: `app/courses/services/assignment_service.py:62-73`

**当前代码**:
```python
# 第63-71行 - 返回字典但不保存
assignment_record = {
    "course_id": assignment_request.course_id,
    "teacher_id": selected_teacher_id,
    "assigned_at": datetime.utcnow(),
    "assigned_by": assigner_id,
    "assignment_type": ("direct" if assignment_request.force_assign else "optimal"),
    "assignment_reason": assignment_request.assignment_reason,
    "evaluation_score": best_teacher["total_score"] if best_teacher else 0.0,
}

return assignment_record  # 返回字典，没有保存到数据库!
```

**CourseAssignment模型已存在**: `app/courses/models/assignment_models.py:35-141`

### 修复方案

1. 导入CourseAssignment模型
2. 创建CourseAssignment对象而不是字典
3. 保存到数据库并commit
4. 返回保存的对象

---

## 三、问题3: AI批改实现缓存逻辑

### 当前问题分析

**文件**: `app/training/services/writing_service.py:1237-1280`

**当前代码**:
```python
# _get_cached_grade: 总是返回None
async def _get_cached_grade(...) -> dict[str, Any] | None:
    logger.info(f"Checking grading cache for key: {cache_key[:8]}...")
    return None  # 总是返回None!

# _set_cached_grade: 只记录日志，不实际缓存
async def _set_cached_grade(...) -> None:
    logger.info(f"Cached grading result for key: {cache_key[:8]}...")
    # 没有实际保存到Redis!
```

**CacheService已存在**: `app/shared/services/cache_service.py`

### 修复方案

1. 导入CacheService
2. 在__init__中初始化cache_service
3. 使用CacheService实现实际缓存

---

## 四、问题4: AI批改实现评分历史

### 当前问题分析

**文件**: `app/training/services/writing_service.py:1321+`

**当前代码**: `_save_grading_history`是stub，只记录日志

**需要的模型**: 需要检查是否有GradingHistory模型

### 修复方案

1. 检查是否有GradingHistory模型
2. 如果没有，创建模型
3. 实现实际保存逻辑

---

## 五、问题5: 通知添加清理Celery任务

### 当前问题分析

**文件**: `app/core/celery_config.py` - 需要添加清理任务

**通知模型已存在**: 有Notification和NotificationHistory模型

### 修复方案

1. 创建通知清理任务
2. 注册到Celery beat schedule
3. 设置定期执行（如每天凌晨3点）

---

## 六、问题1: 实现StudentCourse注册记录

### 当前问题分析

**文件**: `app/courses/services/class_service.py:246-264`

**当前代码**:
```python
# 第246行注释: "创建选课记录（这里简化处理，实际需要ClassStudent表）"
# 只更新了班级学生数，没有创建注册记录!
```

**需要的模型**: StudentCourse/ClassStudent模型不存在

### 修复方案

1. 创建StudentCourse模型
2. 在enroll_student中创建注册记录
3. 实现_check_student_enrollment实际查询
4. 添加课程学生列表查询API

---

## 七、问题6: 实现is_public参数(资源上传)

### 当前问题分析

**文件**: `app/resources/api/v1/resource_endpoints.py:35,152,188`

**当前代码**: is_public参数被接受，在响应中返回，但没有传递给资源创建服务

### 修复方案

1. 确定哪个资源创建端点需要使用此参数
2. 将is_public转换为PermissionLevel
3. 传递给资源创建服务

---

## 修复优先级建议

### 第一批（简单快速）
- 问题2: CourseAssignment持久化 (简单)
- 问题5: 通知清理Celery任务 (简单)
- 问题6: is_public参数 (简单)

### 第二批（中等复杂度）
- 问题3: AI缓存逻辑
- 问题4: AI评分历史

### 第三批（高复杂度）
- 问题1: StudentCourse模型和注册记录

---

## 前置检查

在修复前，请确认:
1. [ ] CacheService可以正常工作
2. [ ] Celery配置正确
3. [ ] 数据库迁移机制可用（Alembic）
4. [ ] 所有模型import正确

---

*本计划基于全量代码审查结果创建*
