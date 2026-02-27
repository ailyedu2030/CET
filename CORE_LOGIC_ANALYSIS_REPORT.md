# CET系统深度逻辑分析完整报告

> 生成日期: 2026-02-27
> 分析范围: 5大核心模块
> 问题总数: 50+

---

## 目录

1. [用户认证模块深度分析](#1-用户认证模块深度分析)
2. [课程管理模块深度分析](#2-课程管理模块深度分析)
3. [AI批改模块深度分析](#3-ai批改模块深度分析)
4. [资源权限模块深度分析](#4-资源权限模块深度分析)
5. [通知系统模块深度分析](#5-通知系统模块深度分析)

---

# 1. 用户认证模块深度分析

## 1.1 登录流程 (Login Flow)

### 代码路径
```
auth_endpoints.py:31-61 (login endpoint)
  ↓
auth_service.py:40-137 (authenticate_user method)
  ↓
jwt_utils.py:112-135 (create_token_pair)
  ↓
jwt_utils.py:164-169 (hash_password)
```

### 完整流程
1. **Line 50-55 (auth_service.py)**: 记录登录尝试 `success=False`
2. **Line 58-59**: 检查账户锁定 `_is_account_locked()`
3. **Line 62-66**: 获取用户 → **发现问题：双重raise死代码**
4. **Line 68-70**: 检查MFA要求
5. **Line 73-78**: MFA启用时返回MFA要求状态
6. **Line 81-85**: 验证 `is_active` 和 `is_verified`
7. **Line 88-89**: 验证 `user_type`
8. **Line 92-93**: 加载用户角色和权限
9. **Line 96-101**: 创建JWT令牌对
10. **Line 104-111**: 创建登录会话
11. **Line 114**: 更新登录统计
12. **Line 117-122**: 更新登录尝试为 `success=True`

### 发现的问题

#### 🔴 CRITICAL: 双重死代码 (auth_service.py:63-66)
```python
# Lines 63-66 - 重复/死代码
if not user:
    raise AuthenticationError("用户名或密码错误", "INVALID_CREDENTIALS")

raise AuthenticationError("用户名或密码错误", "INVALID_CREDENTIALS")  # 永远不执行!
```
第二行永远不会被执行。

#### 🟡 MEDIUM: `remember_me` 字段被忽略
`LoginRequest` schema接受 `remember_me: bool`，但从未使用。

---

## 1.2 Token刷新流程 (Token Refresh Flow)

### 代码路径
```
auth_endpoints.py:70-89 (refresh_token endpoint)
  ↓
auth_service.py:139-158 (refresh_token method)
  ↓
jwt_utils.py:137-157 (refresh_access_token)
```

### 发现的问题

#### 🔴 CRITICAL: 参数不匹配 (auth_endpoints.py:77)
```python
# 端点只传refresh_token
result = await service.refresh_access_token(request.refresh_token)

# 但RefreshTokenRequest要求两个参数
class RefreshTokenRequest(BaseModel):
    refresh_token: str
    session_token: str  # 要求但被忽略!

# 服务方法也期望两个参数
async def refresh_token(self, refresh_token: str, session_token: str)
```

#### 🔴 CRITICAL: 会话验证被绕过
```python
# 会话被获取但只更新last_activity
session = await self._get_active_session(session_token)
if not session or session.refresh_token != refresh_token:
    return None  # 返回None但JWT刷新不验证会话!
```

#### 🔴 CRITICAL: 刷新后权限丢失 (jwt_utils.py:148-154)
```python
new_token_data = {
    "sub": payload.get("sub"),
    "username": payload.get("username"),
    "user_type": payload.get("user_type"),
    "roles": payload.get("roles", []),  # 可能为空!
    "permissions": payload.get("permissions", {}),  # 不在refresh token中!
}
```
刷新后的access token权限为空。

---

## 1.3 登出流程 (Logout Flow)

### 代码路径
```
auth_endpoints.py:98-125 (logout endpoint)
  ↓
jwt_utils.py:97-100 (extract_jti)
  ↓
token_blocklist_service.py:29-37 (add_to_blocklist)
```

### 发现的问题

#### 🔴 CRITICAL: Refresh Token未被加入黑名单
```python
# 只添加了access token的JTI
token = auth_header[7:]  # 这是ACCESS TOKEN
jti = jwt_manager.extract_jti(token)
await token_blocklist_service.add_to_blocklist(jti, ttl)

# Refresh Token从未被加入黑名单!
```
攻击者持有refresh token仍可生成新access token!

---

## 1.4 密码修改流程 (Password Change Flow)

### 流程
1. 获取用户
2. 验证旧密码
3. 验证新密码长度
4. 检查密码历史（防止最近5个密码）
5. 更新密码哈希
6. 使所有会话失效

### 发现的问题

#### 🟡 MEDIUM: 无密码复杂度验证
```python
if len(new_password) < settings.PASSWORD_MIN_LENGTH:  # 只检查长度!
    return False
```

---

## 1.5 注册流程 (Registration Flow)

### 发现的问题

#### 🟡 MEDIUM: 邮箱验证被绕过 (registration_service.py:267-268)
```python
user.is_active = True
user.is_verified = True  # 管理员审批后直接激活，未点击邮箱验证链接!
```

---

# 2. 课程管理模块深度分析

## 2.1 课程创建流程

### 代码路径
```
course_endpoints.py:32-48 → create_course()
course_service.py:32-68 → CourseService.create_course()
```

### 发现的问题

| 问题 | 位置 | 严重程度 |
|------|------|---------|
| 无角色验证 | course_endpoints.py:35 | HIGH |
| 模板继承无验证 | course_service.py:42-49 | HIGH |
| 默认状态不安全 | course_models.py:73 | HIGH |

#### 🔴 HIGH: 任何用户可创建课程
```python
# course_endpoints.py:35 - 无角色检查!
@router.post("/courses/", ...)
async def create_course(...):
    # 任何认证用户都可以创建，包括学生!
```

---

## 2.2 学生注册流程

### 代码路径
```
class_endpoints.py:234-273 → enroll_student()
class_service.py:227-264 → ClassService.enroll_student()
```

### 发现的问题

#### 🔴 CRITICAL: 未创建注册记录
```python
# class_service.py:246
# 简化处理 - 没有创建实际的注册记录!
# 只增加计数器，没有StudentCourse表记录
```

#### 🔴 CRITICAL: 重复注册检查永远返回False
```python
# class_service.py:435
def _check_student_enrollment(...) -> bool:
    return False  # 永远返回False!
```

---

## 2.3 课程分配流程

### 发现的问题

#### 🔴 CRITICAL: 分配记录未持久化
```python
# assignment_service.py:62-73
# 返回dict但从未保存到CourseAssignment表!
# 数据丢失!
```

#### 🔴 HIGH: 教师资格检查使用假数据
```python
# course_assignment_service.py:428-432
# 硬编码值 - 不查询实际教师资料
```

---

## 2.4 评分流程

### 发现的问题

| 问题 | 严重程度 |
|------|---------|
| 评分可见性规则不明确 | HIGH |
| 评分修改无审计追踪 | HIGH |
| 无评分申诉机制 | MEDIUM |
| 置信度阈值过低 | MEDIUM |

---

## 2.5 班级管理流程

### 发现的问题

#### 🔴 HIGH: 教师可创建班级
```python
# class_endpoints.py:36
# 无管理员检查 - 任何教师都可创建班级
```

---

# 3. AI批改模块深度分析

## 3.1 写作提交流程

### 代码路径
```
writing_endpoints.py:243-261 → POST /submissions
writing_service.py:226-259 → WritingService.submit_essay()
```

### 发现的问题

#### 🔴 CRITICAL: 函数返回两次
```python
# writing_service.py:256-259
# submit_essay函数有重复代码 - 返回两次!
```

---

## 3.2 AI评分流程

### 代码路径
```
writing_service.py:261-351 → _grade_essay()
deepseek_service.py → DeepSeek API调用
```

### 发现的问题

#### 🔴 CRITICAL: 缓存方法是STUB
```python
# writing_service.py:1237-1279
async def _get_cached_grade(self, content: str) -> Optional[dict]:
    # 这只是stub - 实际上没有实现Redis缓存!
    return None  # 总是返回None

async def _set_cached_grade(self, content: str, grade_result: dict):
    # 只是记录日志，没有实际缓存
    logger.info("Cache set called (not implemented)")
```

#### 🔴 CRITICAL: 评分历史未实现
```python
# writing_service.py:1321-1340
async def _save_grading_history(self, ...):
    # 只是stub - 没有实际保存到数据库!
    logger.info("Grading history saved (not implemented)")
```

---

## 3.3 重复检测流程

### 发现的问题

#### 🟡 MEDIUM: 重复检测逻辑不完整
- 使用简单的MD5哈希比较
- 未考虑语义相似度
- 未实现实际缓存

---

# 4. 资源权限模块深度分析

## 4.1 资源上传流程

### 代码路径
```
resource_endpoints.py:29-204 → upload_document()
resource_library_service.py:151-235 → create_resource()
```

### 发现的问题

#### 🔴 CRITICAL: is_public参数被忽略
```python
# resource_endpoints.py:35
is_public: bool = Form(False)  # 接受参数但不使用!

# resource_library_service.py:188
# 总是设置为PRIVATE，忽略is_public
permission_level = PermissionLevel.PRIVATE
```

---

## 4.2 资源分享流程

### 发现的问题

#### 🔴 CRITICAL: shared_by=0 硬编码
```python
# permission_service.py:375
shared_by=0,  # TODO:获取当前用户ID
# 所有分享都显示为系统用户!
```

#### 🔴 CRITICAL: CLASS权限检查为空
```python
# permission_service.py:119-121
and_(
    ResourceLibrary.permission_level == PermissionLevel.CLASS,
),
# 条件为空 - 没有验证用户是否在分享的班级中!
```

---

## 4.3 权限继承

### 状态: 未实现

资源不从课程继承权限。

---

## 4.4 权限撤销

### 发现的问题

#### 🔴 HIGH: 教师分享未被撤销
```python
# permission_service.py:390
share_scope="private"  # 教师分享

# _clear_class_sharing()只删除scope="class"
# 教师分享永远不会被撤销!
```

---

# 5. 通知系统模块深度分析

## 5.1 通知创建流程

### 代码路径
```
notification_endpoints.py → UnifiedNotificationService.send_notification()
notification_service.py:33-101
```

### 发现的问题

#### 🔴 HIGH: 无事务原子性
- 批量发送时部分失败无回滚
- WebSocket发送失败后无法恢复

---

## 5.2 WebSocket推送流程

### 🔴 CRITICAL: WebSocket未与通知创建集成!

```python
# notification_service.py:33-101
# 创建通知后:
# - 保存到数据库 ✓
# - 发送邮件 ✓
# - 发送短信 ✓
# - 推送通知 ✓
# - WebSocket推送 ✗ 从未调用!
```

WebSocket管理器有方法:
- `send_notification_to_user()` 
- `send_notification_to_users()`

**但这些从未被调用!**

这意味着:
1. 通知存储到数据库
2. 用户必须通过 `/notifications/list` API轮询
3. 实时WebSocket推送**不触发**

---

## 5.3 通知偏好流程

### 发现的问题

| 问题 | 状态 |
|------|------|
| per-type preferences | 已定义但未使用 |
| max_daily_notifications | 已定义但未实施 |
| batch_similar_notifications | 已定义但未实现 |

---

## 5.4 批量通知流程

### 发现的问题

#### 🔴 CRITICAL: 班级通知只发送教师
```python
# notification_service.py:517-519
# 获取班级的学生（通过课程注册关系）
# 这里需要根据实际的数据模型调整
# 暂时返回教师ID，后续可以扩展学生查询逻辑
# 学生永远收不到通知!
```

---

## 5.5 通知清理流程

### 🔴 CRITICAL: 清理任务不存在!

- 无自动化清理任务
- 无TTL/保留策略
- 通知永久保存
- 数据库将无限增长

---

# 问题汇总表

| 模块 | 严重程度 | 问题数 |
|------|---------|-------|
| 用户认证 | CRITICAL | 7 |
| 课程管理 | CRITICAL | 17+ |
| AI批改 | CRITICAL | 8 |
| 资源权限 | CRITICAL | 8 |
| 通知系统 | CRITICAL | 10 |

---

# 建议修复计划

## P0 - 立即修复

1. **认证**: 删除auth_service.py死代码
2. **认证**: 修复session_token参数传递
3. **权限**: 实现is_public参数
4. **权限**: 实现CLASS成员验证
5. **通知**: 集成WebSocket推送

## P1 - 高优先级

6. **课程**: 实现StudentCourse注册记录
7. **课程**: 持久化CourseAssignment
8. **AI批改**: 实现缓存逻辑
9. **AI批改**: 实现评分历史
10. **通知**: 添加清理Celery任务

## P2 - 中优先级

11. 实现密码复杂度验证
12. 实现权限继承
13. 实现评分可见性规则
14. 实现偏好功能

---

*报告生成时间: 2026-02-27*
*分析工具: oh-my-opencode Explore Agent*
