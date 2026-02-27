# CET深度审计修复计划

## 一、审计概述

基于深度功能审计，发现以下模块存在实现问题：

| 模块 | API端点 | 服务函数 | 发现问题数 |
|------|---------|---------|-----------|
| users | 50+ | 50+ | 7 |
| courses | 112+ | 40+ | 待细分 |
| training | 200+ | 80+ | 15+ |
| resources | 60+ | 50+ | 12+ |
| notifications | 17 | 14 | 6 |
| shared | - | 6 | 2 |

---

## 二、新发现问题汇总（按优先级）

### 🔴 CRITICAL - 必须立即修复

#### 1. 用户模块 - 死代码
- **文件**: `app/users/services/auth_service.py:64-66`
- **问题**: 双重raise语句，第二行永不到达
- **代码**:
```python
if not user:
    raise AuthenticationError("用户名或密码错误", "INVALID_CREDENTIALS")
# 永不到达!
raise AuthenticationError("用户名或密码错误", "INVALID_CREDENTIALS")
```
- **修复**: 删除第66行

#### 2. 通知模块 - 3个端点缺少认证（安全漏洞）
- **文件**: `app/notifications/api/v1/notification_endpoints.py`
- **问题**: 以下端点缺少身份验证，任何人可调用
  - Line 279-302: `POST /notifications/teaching-plan-change`
  - Line 305-328: `POST /notifications/training-anomaly-alert`
  - Line 331-354: `POST /notifications/resource-audit`
- **修复**: 添加 `dependencies=[AuthRequired()]`

#### 3. 资源模块 - 硬编码用户ID
- **文件**: `app/resources/services/permission_service.py:375`
- **问题**: `shared_by=0` 硬编码，应获取当前用户ID
- **修复**: 从current_user获取用户ID

#### 4. 资源模块 - 管理员权限检查被注释
- **文件**: `app/resources/api/v1/resource_endpoints.py:1053-1055`
- **问题**: rebuild-vectors端点的管理员权限检查被注释
- **修复**: 取消注释并验证

---

### 🟠 HIGH - 高优先级

#### 5. 用户模块 - 未验证用户可访问
- **文件**: `app/users/utils/auth_decorators.py:86-92`
- **问题**: `get_current_active_user`只检查is_active，未检查is_verified
- **影响**: 未验证邮箱的用户可以访问需认证的端点
- **修复**: 添加is_verified检查

#### 6. 用户模块 - 外键指定错误
- **文件**: `app/users/models/user_models.py:543-546`
- **问题**: RegistrationApplication的user关系使用模糊的foreign_keys
- **修复**: 明确指定user_id

#### 7. 用户模块 - 枚举vs字符串
- **文件**: `app/users/api/v1/registration_endpoints.py:365`
- **问题**: `user_type.value != "admin"` 应使用UserType.ADMIN
- **修复**: 改为枚举比较

#### 8. 用户模块 - 方法名错误
- **文件**: `app/users/services/auth_service.py:721`
- **问题**: 调用`jwt_manager.get_password_hash()`但方法名是`hash_password()`
- **修复**: 更正方法名

#### 9. 训练模块 - 多个Stub返回假数据
- **文件**: `app/training/api/v1/adaptive_learning_endpoints.py`
- **问题**: 以下方法返回硬编码假数据:
  - Line 322-341: `auto_collect_error()` - 返回假error_id
  - Line 744-754: `start_error_practice()` - 返回假session_id
  - Line 776-780: `mark_question_mastered()` - 简化实现
  - Line 802-806: `reset_error_status()` - 简化实现
- **修复**: 实现真实数据库操作

#### 10. 训练模块 - 11个服务返回空{}
- **问题**: 以下服务返回空字典而非数据库查询:
  - `error_analysis_service.py`
  - `assistant_service.py`
  - `real_time_monitoring_service.py`
  - `forgetting_curve_service.py`
  - `achievement_service.py`
  - `ai_analysis_service.py`
  - `reminder_utils.py`
  - `intelligent_alert_service.py`
  - `progress_tracker.py`
  - `data_analyzer.py`
  - `knowledge_graph.py`
- **修复**: 实现真实数据库查询

#### 11. 资源模块 - 计方法返回0
- **文件**: `app/resources/services/course_resource_service.py`
- **问题**:
  - Line 390: `_get_vocabulary_count()` 返回 0
  - Line 394: `_get_knowledge_point_count()` 返回 0
- **修复**: 实现真实计数查询

#### 12. 资源模块 - 方法返回空列表
- **文件**: `app/resources/services/resource_library_service.py`
- **问题**:
  - Line 1078: `get_comments()` 返回 []
  - Line 1344: `get_all_tags()` 返回 []
  - Line 1385: `get_categories()` 返回 []
  - Line 1390: `get_category_tree()` 返回 []
- **修复**: 实现数据库查询

---

### 🟡 MEDIUM - 中优先级

#### 13. 训练模块 - 权限检查不一致
- **问题**: 混用枚举和字符串比较
  - `training_workshop_endpoints.py:156` 使用字符串 `"teacher"`
  - `adaptive_learning_endpoints.py` 使用字符串 `"teacher", "admin"`
- **修复**: 统一使用UserType枚举

#### 14. 训练模块 - 分页问题
- **文件**: `app/training/api/v1/training_endpoints.py:196-205`
- **问题**: 使用`len(questions)`而非数据库COUNT
- **修复**: 使用SQL COUNT

#### 15. 通知模块 - _get_target_users不完整
- **文件**: `app/notifications/services/notification_service.py:500-523`
- **问题**: 只返回教师ID，未包含学生
- **注释**: "暂时返回教师ID，后续可以扩展学生查询逻辑"
- **修复**: 添加学生查询逻辑

#### 16. 训练模块 - 助手端点返回Mock数据
- **文件**: `app/training/api/v1/assistant_endpoints.py`
- **问题**:
  - Line 403-443: `get_learning_suggestions()` 返回mock
  - Line 446-483: `get_learning_analytics()` 返回mock

---

### 🟢 LOW - 低优先级

#### 17. 用户模块 - id_number可为null
- **文件**: `app/users/models/user_models.py:176-181`
- **问题**: StudentProfile.id_number唯一但可为空
- **建议**: 考虑设为必填

#### 18. 资源模块 - knowledge_service返回空
- **问题**: 多个方法返回空列表 (lines 202, 227, 256, 274)

#### 19. 资源模块 - semantic_search_service返回空
- **问题**: 多个方法返回空列表或默认值

#### 20. 资源模块 - vector_search_service返回空
- **问题**: 多个stub方法返回空集合

#### 21. Shared模块 - cleanup未实现
- **文件**: `app/shared/models/learning_mixins.py:336-368`
- **问题**: `cleanup_expired_data()` 方法是stub

---

## 三、修复顺序建议

### 第一批（立即修复 - 1小时内）
1. [CRITICAL-1] 删除auth_service.py死代码
2. [CRITICAL-2] 通知模块添加认证（3个端点）
3. [CRITICAL-3] permission_service.py硬编码用户ID

### 第二批（高优先级 - 半天）
4. [HIGH-1] auth_decorators.py添加is_verified检查
5. [HIGH-2] 修复外键指定
6. [HIGH-3] 统一枚举vs字符串
7. [HIGH-4] 修正方法名
8. [HIGH-5-6] 训练模块stub实现

### 第三批（中优先级 - 1天）
9. [MEDIUM-1] 统一权限检查枚举
10. [MEDIUM-2] 分页COUNT修复
11. [MEDIUM-3] 通知服务学生查询
12. [MEDIUM-4] 助手端点实现

### 第四批（低优先级 - 待定）
13-21. 其他改进

---

## 四、验证要求

每个修复必须验证：
1. **语法正确**: `python -m py_compile`
2. **导入正确**: 所有模块可正常导入
3. **逻辑正确**: 代码逻辑符合预期
4. **测试通过**: 相关测试用例通过

---

## 五、关联原有96问题

本次审计发现的新问题与原有96问题不重复：
- 原有96问题: 侧重于缺失功能、配置不一致
- 新审计问题: 侧重于实现不完整、stub代码、安全漏洞

建议分别跟踪修复进度。
