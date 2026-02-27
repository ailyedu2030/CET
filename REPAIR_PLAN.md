# CET系统完整修复计划

## 一、修复原则

1. **全量修复**: 不跳跃、不简化、不畏惧工作量
2. **科学严谨**: 按依赖关系、按优先级顺序修复
3. **完整验证**: 每个修复后必须验证
4. **零技术债务**: 修复后代码质量必须达标
5. **100%完成**: 所有96个问题必须修复

## 二、修复阶段划分

### 阶段一: 基础层修复 (依赖最底层)
- **目标**: 修复数据库模型、配置、工具层
- **问题数**: 15个
- **预计时间**: 2天
- **验证标准**: 所有基础层测试通过

### 阶段二: 核心功能层修复
- **目标**: 修复用户认证、课程管理、资源管理
- **问题数**: 66个 (18+20+28)
- **预计时间**: 5天
- **验证标准**: 核心功能100%可用

### 阶段三: 训练功能层修复
- **目标**: 修复写作训练、听力训练、AI批改
- **问题数**: 30个 (8+22)
- **预计时间**: 3天
- **验证标准**: 训练流程完整可用

### 阶段四: 增强功能层修复
- **目标**: 修复自适应学习、学习计划、社交学习
- **问题数**: 待审查
- **预计时间**: 2天

### 阶段五: 完善与优化
- **目标**: 性能优化、代码质量、文档完善
- **问题数**: 12个LOW优先级
- **预计时间**: 1天

**总预计时间**: 13天
**总问题数**: 96个

## 三、详细修复清单

### 模块1: 用户认证 (18个问题)

#### 1.1 CRITICAL (4个) - 必须立即修复

**问题1: 密码最小长度不一致**
- **文件**: `app/users/schemas/auth_schemas.py:17`
- **问题**: schema允许6字符，config要求8字符
- **修复步骤**:
  1. 修改auth_schemas.py:17，将min_length=6改为8
  2. 修改registration_schemas.py:18，将min_length=6改为8
  3. 验证: 尝试用7字符密码注册，应返回400错误
  4. 验证: 用8字符密码注册，应成功
- **验证标准**: ✅ 7字符密码被拒绝，8字符密码被接受

**问题2: 缺少refresh token端点**
- **文件**: `app/users/api/v1/auth_endpoints.py` (缺失)
- **问题**: RefreshTokenRequest/Response存在但无对应endpoint
- **修复步骤**:
  1. 在auth_endpoints.py添加POST /refresh-token端点
  2. 实现逻辑: 验证refresh token → 生成新access token
  3. 调用AuthService.refresh_token()方法
  4. 返回格式: {access_token, refresh_token, token_type}
- **代码实现**:
```python
@router.post("/refresh-token", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> RefreshTokenResponse:
    service = AuthService(db)
    result = await service.refresh_token(request.refresh_token)
    return RefreshTokenResponse(**result)
```
- **验证标准**: ✅ 使用有效refresh token能获取新access token
- **验证标准**: ✅ 使用无效refresh token返回401错误

**问题3: 刷新token后丢失角色/权限**
- **文件**: `app/users/utils/jwt_utils.py:116-133`
- **问题**: refresh_access_token()只保留sub和username，丢失roles
- **修复步骤**:
  1. 修改refresh_access_token()方法
  2. 保留所有必要字段: sub, username, user_type, roles, permissions
  3. 确保新token包含完整的用户上下文
- **代码实现**:
```python
new_token_data = {
    "sub": payload.get("sub"),
    "username": payload.get("username"),
    "user_type": payload.get("user_type"),
    "roles": payload.get("roles", []),
    "permissions": payload.get("permissions", {})
}
```
- **验证标准**: ✅ 刷新token后，新token包含原始roles和permissions
- **验证标准**: ✅ 使用刷新后的token访问受保护路由，权限不变

**问题4: SECRET_KEY为空允许启动**
- **文件**: `app/core/config.py:21, 169-184`
- **问题**: SECRET_KEY默认为空字符串，validate()方法未被调用
- **修复步骤**:
  1. 修改config.py:21，移除默认值
  2. 在app/main.py启动时调用settings.validate()
  3. 如果SECRET_KEY为空或长度<32，抛出ValueError
- **代码实现**:
```python
# In app/main.py
from app.core.config import settings

@app.on_event("startup")
async def startup_event():
    settings.validate()  # This will raise if SECRET_KEY is invalid
```
- **验证标准**: ✅ 未设置SECRET_KEY时，应用启动失败并显示明确错误
- **验证标准**: ✅ 设置有效SECRET_KEY后，应用正常启动

#### 1.2 HIGH (6个) - 重要功能修复

**问题5: 登录未捕获IP/user-agent用于审计**
- **文件**: `app/users/api/v1/auth_endpoints.py:42-46`
- **问题**: authenticate_user()调用未传递IP和user_agent
- **修复步骤**:
  1. 从request对象获取client_host和user_agent
  2. 传递给authenticate_user()方法
  3. AuthService应记录这些信息到LoginAttempt表
- **代码实现**:
```python
# In auth_endpoints.py:login()
ip_address = request.client.host if request.client else None
user_agent = request.headers.get("user-agent")

result = await service.authenticate_user(
    username=request.username,
    password=request.password,
    user_type=request.user_type.value if request.user_type else None,
    ip_address=ip_address,
    user_agent=user_agent
)
```
- **验证标准**: ✅ 登录成功后，LoginAttempt表包含IP和user_agent

**问题6: 登出未使token失效(无blocklist)**
- **文件**: `app/users/api/v1/auth_endpoints.py:75-87`
- **问题**: JWT是stateless的，logout只是标记session，token仍然有效
- **修复步骤**:
  1. 实现TokenBlocklist服务，使用Redis存储
  2. logout时将token jti加入blocklist，设置过期时间
  3. get_current_user()验证时检查blocklist
- **代码实现**:
```python
# In auth_service.py:logout()
async def logout(self, token: str) -> None:
    jti = self._extract_jti(token)
    await self.token_blocklist.add(jti, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

# In dependencies.py:get_current_user()
if await token_blocklist.is_blocked(jti):
    raise HTTPException(status_code=401, detail="Token has been revoked")
```
- **验证标准**: ✅ 登出后，相同token再次访问返回401
- **验证标准**: ✅ 登出后，使用新token可以正常访问

**问题7: 限流username+IP一起检查 - 共享IP会封所有人**
- **文件**: `app/users/services/auth_service.py:281-296`
- **问题**: 限流查询同时检查username和IP，导致共享IP的所有用户被封
- **修复步骤**:
  1. 分开检查username和IP的限流
  2. 任一达到限制就触发封禁
  3. 记录时分开记录username和IP的尝试
- **代码实现**:
```python
# Check username attempts
username_attempts = await self.db.execute(
    select(LoginAttempt).where(
        LoginAttempt.username == username,
        LoginAttempt.created_at >= datetime.utcnow() - timedelta(minutes=15)
    )
)

# Check IP attempts  
ip_attempts = await self.db.execute(
    select(LoginAttempt).where(
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.created_at >= datetime.utcnow() - timedelta(minutes=15)
    )
)

if username_attempts.count() >= 5 or ip_attempts.count() >= 20:
    # Block
```
- **验证标准**: ✅ 同一IP下，用户A失败5次被封，用户B仍可正常登录
- **验证标准**: ✅ IP失败20次后，该IP所有用户被封

**问题8: MFA配置存在但未强制执行**
- **文件**: `app/core/config.py:29-31`, `app/users/services/auth_service.py:59-85`
- **问题**: MFA_REQUIRED配置存在但login()不检查
- **修复步骤**:
  1. login()验证密码后，检查settings.MFA_REQUIRED
  2. 如果为True且用户未设置MFA，返回错误要求设置MFA
  3. 如果已设置MFA，返回状态要求第二步验证
- **代码实现**:
```python
# In auth_service.py:authenticate_user()
if settings.MFA_REQUIRED and not user.mfa_enabled:
    raise ValueError("MFA is required but not configured for this user")

if user.mfa_enabled:
    # Generate MFA token and send
    mfa_token = await self._generate_mfa_token(user.id)
    return {"status": "mfa_required", "mfa_token": mfa_token}
```
- **验证标准**: ✅ MFA_REQUIRED=True时，未设置MFA的用户无法登录
- **验证标准**: ✅ MFA_REQUIRED=False时，所有用户可以正常登录

**问题9: 无邮箱验证流程**
- **文件**: `app/users/services/registration_service.py:73-74`
- **问题**: 用户创建时is_verified=False，但没有验证流程
- **修复步骤**:
  1. 用户注册时生成邮箱验证token
  2. 发送验证邮件到用户邮箱
  3. 提供/api/v1/users/verify-email端点验证token
  4. 验证后设置is_verified=True
- **代码实现**:
```python
# In registration_service.py
verification_token = jwt_manager.create_verification_token(user.id, user.email)
await email_service.send_verification_email(user.email, verification_token)

# New endpoint
@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    user_id = jwt_manager.verify_verification_token(token)
    user = await user_service.get_user_by_id(user_id)
    user.is_verified = True
    await db.commit()
```
- **验证标准**: ✅ 注册后用户收到验证邮件
- **验证标准**: ✅ 点击验证链接后，用户is_verified变为True

**问题10: 改邮箱无需重新验证**
- **文件**: `app/users/services/auth_service.py:415-451`
- **问题**: update_user_profile()允许修改email且无需重新验证
- **修复步骤**:
  1. 修改email时，设置is_verified=False
  2. 发送验证邮件到新邮箱
  3. 在新邮箱点击验证链接后，才设置is_verified=True
- **代码实现**:
```python
# In auth_service.py:update_user_profile()
if "email" in update_data and update_data["email"] != user.email:
    user.email = update_data["email"]
    user.is_verified = False
    # Send verification email
    verification_token = jwt_manager.create_verification_token(user.id, user.email)
    await email_service.send_verification_email(user.email, verification_token)
```
- **验证标准**: ✅ 修改邮箱后，is_verified变为False
- **验证标准**: ✅ 必须在新邮箱点击验证链接后，is_verified才变为True

#### 1.3 MEDIUM (6个) - 优化改进

**问题11: 添加密码历史检查**
- **文件**: `app/users/services/auth_service.py:189-215`
- **修复**: 修改密码时检查新密码是否与最近5次密码相同
- **实现**: 存储密码历史hash，修改时检查

**问题12: 实现会话固定防护**
- **文件**: `app/users/services/auth_service.py:85-93`
- **修复**: 登录后使所有旧session token失效
- **实现**: login()时将所有旧session标记为无效

**问题13: 添加密码过期字段**
- **文件**: `app/users/models/user_models.py:57-61`
- **修复**: 添加password_changed_at字段，强制定期修改密码
- **实现**: 添加字段，login()检查是否过期

**问题14: 实现并发登录限制**
- **文件**: `app/users/services/auth_service.py`
- **修复**: 限制同一用户同时活跃session数量
- **实现**: 检查活跃session数，超过限制则拒绝新登录

**问题15: 添加登录审计日志**
- **文件**: `app/users/services/auth_service.py:42-46`
- **修复**: 记录所有登录尝试到审计表
- **实现**: 创建LoginAudit表，记录成功/失败、IP、时间

**问题16: 实现账户锁定机制**
- **文件**: `app/users/services/auth_service.py:281-296`
- **修复**: 连续失败达到一定次数，锁定账户一段时间
- **实现**: 添加locked_until字段，失败时检查并锁定

#### 1.4 LOW (2个) - 完善性修复

**问题17: 添加安全事件通知**
- **修复**: 检测到异常登录时发送通知给用户
- **实现**: 检查IP地理位置变化，发送邮件/短信通知

**问题18: 实现设备管理**
- **修复**: 允许用户查看和管理登录设备
- **实现**: 创建设备表，提供API查看/撤销设备

---

### 模块2: 课程管理 (20个问题)

#### 2.1 CRITICAL (3个) - 必须立即修复

**问题1: 修复分页性能问题**
- **文件**: `app/courses/services/course_service.py:414-439`
- **问题**: get_accessible_courses()加载所有课程到内存再切片
- **修复**: 使用数据库级别的LIMIT/OFFSET
- **代码实现**:
```python
# Before (line 438):
return accessible_courses[skip:skip + limit]

# After:
query = query.offset(skip).limit(limit)
result = await self.db.execute(query)
return result.scalars().all()
```
- **验证标准**: ✅ 10000门课程时，响应时间<100ms

**问题2: 添加事务回滚**
- **文件**: `app/courses/services/course_service.py:44-48`
- **问题**: create_course()先commit course，再创建version，如果version失败，orphan course残留
- **修复**: 使用async transaction，确保原子性
- **代码实现**:
```python
async with self.db.begin():
    course = Course(**course_data)
    self.db.add(course)
    await self.db.flush()
    await self._create_initial_version(course, creator_id)
# If _create_initial_version fails, whole transaction rolls back
```
- **验证标准**: ✅ version创建失败时，course也被回滚

**问题3: 修复版本创建逻辑**
- **文件**: `app/courses/services/course_service.py:100-110`
- **问题**: update_course()总是创建新版本，即使数据未改变
- **修复**: 比较新旧数据，只有实际变化时才创建版本
- **代码实现**:
```python
# Before (line 97):
await self._create_version_snapshot(course_id, updater_id)

# After:
has_changes = any(
    getattr(course, field) != update_data[field]
    for field in update_data
)
if has_changes:
    await self._create_version_snapshot(course_id, updater_id)
```
- **验证标准**: ✅ 无变化时，不创建新版本

#### 2.2 HIGH (8个) - 重要功能修复

**问题4: 实现软删除级联**
- **文件**: `app/courses/services/course_service.py:165-170`
- **问题**: delete_course()只更新status，不删除关联数据
- **修复**: 软删除时，级联更新关联表status
- **实现**: 添加ondelete='CASCADE'到ForeignKey，或使用事件监听器

**问题5: 修复状态转换验证**
- **文件**: `app/courses/services/course_service.py:257-287`
- **问题**: PREPARING不能直接到PUBLISHED，但错误信息不明确
- **修复**: 添加详细的错误消息，指导用户正确操作
- **实现**: 
```python
if current_status == CourseStatus.PREPARING and new_status == CourseStatus.PUBLISHED:
    raise ValueError("课程必须先提交审核(DRAFT→REVIEWING)，审核通过后才能发布")
```

**问题6: 添加唯一性验证**
- **文件**: `app/courses/services/course_service.py:44-48`
- **问题**: create_course()不检查code唯一性
- **修复**: 创建前检查code是否已存在
- **实现**: 
```python
existing = await self.db.execute(select(Course).where(Course.code == course_data["code"]))
if existing.scalar():
    raise ValueError(f"课程代码 {course_data['code']} 已存在")
```

**问题7: 修复schema字段缺失**
- **文件**: `app/courses/schemas/course_schemas.py:55-71`
- **问题**: CourseResponse缺少created_by字段
- **修复**: 添加created_by: int字段
- **实现**: `created_by: int = Field(..., description="创建人ID")`

**问题8: 实现数据库分页**
- **文件**: `app/courses/services/course_service.py:414-439`
- **问题**: get_accessible_courses()无分页参数
- **修复**: 添加skip, limit参数，使用数据库分页
- **实现**: 见问题1

**问题9: 修复权限检查顺序**
- **文件**: `app/courses/services/course_service.py:62-76`
- **问题**: get_course()先检查权限再检查存在性，导致信息泄露
- **修复**: 先检查course存在性，再检查权限
- **实现**: 
```python
course = await self.db.get(Course, course_id)
if not course:
    raise ResourceNotFoundError("课程不存在")

if not await self._check_course_access(course_id, user_id):
    raise PermissionDeniedError("无权限访问此课程")
```

**问题10: 添加课程复制验证**
- **文件**: `app/courses/services/course_service.py:226-250`
- **问题**: duplicate_course()不验证new_name唯一性
- **修复**: 复制前检查新名称是否已存在
- **实现**: 
```python
existing = await self.db.execute(select(Course).where(Course.name == new_name))
if existing.scalar():
    raise ValueError(f"课程名称 {new_name} 已存在")
```

#### 2.3 MEDIUM (7个) - 优化改进

**问题11: 修复rollback字段完整性**
- **文件**: `app/courses/services/course_service.py:211-218`
- **问题**: rollback_course_version()不恢复所有字段
- **修复**: 恢复所有字段，包括target_audience, difficulty_level等
- **实现**: 从version_snapshot读取所有字段并更新

**问题12: 实现版本冲突检测**
- **文件**: `app/courses/services/course_service.py:100-110`
- **问题**: 并发更新可能导致版本冲突
- **修复**: 添加乐观锁，使用version字段检测冲突
- **实现**: 
```python
if course.version != update_data.get("version"):
    raise ConflictError("课程已被其他人修改，请刷新后重试")
```

**问题13: 添加课程归档功能**
- **文件**: `app/courses/models/course_models.py:140-151`
- **问题**: 无归档状态，删除后无法恢复
- **修复**: 添加ARCHIVED状态，提供归档/恢复功能
- **实现**: 添加status=ARCHIVED，提供archive()/unarchive()方法

**问题14: 修复批量操作性能**
- **文件**: `app/courses/services/course_service.py:414-439`
- **问题**: 批量操作无事务，可能部分成功
- **修复**: 使用async transaction确保原子性
- **实现**: 
```python
async with self.db.begin():
    for course_id in course_ids:
        await self._update_single_course(course_id, update_data)
```

**问题15: 实现课程模板继承**
- **文件**: `app/courses/models/course_models.py:679-720`
- **问题**: 模板和课程无关联，无法继承
- **修复**: 添加template_id外键，实现字段继承
- **实现**: 添加template_id = Column(Integer, ForeignKey('course_templates.id'))

**问题16: 添加课程统计分析**
- **文件**: `app/courses/services/course_service.py` (缺失)
- **问题**: 无课程统计功能
- **修复**: 添加get_course_stats()方法，统计学生数、完成率等
- **实现**: 
```python
async def get_course_stats(self, course_id: int) -> dict:
    student_count = await self.db.execute(
        select(func.count(StudentCourse.student_id))
        .where(StudentCourse.course_id == course_id)
    )
    completion_rate = await self._calculate_completion_rate(course_id)
    return {"student_count": student_count, "completion_rate": completion_rate}
```

**问题17: 修复课程关联数据**
- **文件**: `app/courses/models/course_models.py:140-151`
- **问题**: 软删除课程时，关联数据未处理
- **修复**: 添加cascade='all, delete-orphan'或手动处理
- **实现**: 使用SQLAlchemy事件@event.listens_for(Course, 'before_update')

**问题18: 实现课程导入导出**
- **文件**: `app/courses/services/course_service.py` (缺失)
- **问题**: 无导入导出功能
- **修复**: 添加export_course()/import_course()方法
- **实现**: 导出为JSON格式，包含课程所有信息和关联数据

#### 2.4 LOW (2个) - 完善性修复

**问题19: 添加课程审核流程**
- **文件**: `app/courses/api/v1/course_endpoints.py` (缺失)
- **问题**: 无审核流程，任何人可发布课程
- **修复**: 添加审核状态，提供submit_for_review()/approve()/reject()方法
- **实现**: 添加REVIEWING, APPROVED, REJECTED状态，只有ADMIN可审核

**问题20: 修复课程搜索功能**
- **文件**: `app/courses/services/course_service.py:414-439`
- **问题**: 搜索功能简单，不支持高级搜索
- **修复**: 添加全文搜索，支持按标签、难度、分类搜索
- **实现**: 使用PostgreSQL全文搜索或Elasticsearch

---

### 模块3: 写作训练+AI批改 (8个问题)

#### 3.1 CRITICAL (2个) - 必须立即修复

**问题1: _grade_essay方法有死代码**
- **文件**: `app/training/services/writing_service.py:275-283`
- **问题**: 两个if块检查相同条件，第一个冗余
- **修复**: 删除第一个if块，保留第二个
- **代码实现**:
```python
# 删除以下代码 (lines 275-281):
if success and ai_response and isinstance(ai_response, dict) and "choices" in ai_response:
    content = str(ai_response["choices"][0]["message"]["content"])
    grading_result = self._parse_grading_result(content)
    submission.total_score = grading_result["total_score"]
    # Line 281 is empty

# Keep only (lines 283-310):
if ai_response and isinstance(ai_response, dict) and "choices" in ai_response:
    content = str(ai_response["choices"][0]["message"]["content"])
    grading_result = self._parse_grading_result(content)
    # ... rest of the logic
```
- **验证标准**: ✅ 代码覆盖率不变，功能正常

**问题2: 提交后未刷新数据**
- **文件**: `app/training/services/writing_service.py:249-253`
- **问题**: submit_essay()调用_grade_essay()后，返回的submission对象未刷新，分数为旧值
- **修复**: _grade_essay()后刷新submission对象
- **代码实现**:
```python
# After line 249:
await self._grade_essay(submission)
await self.db.refresh(submission)  # Add this line
logger.info(f"作文提交成功: ID={submission.id}")
return submission
```
- **验证标准**: ✅ 返回的submission.total_score是AI评分后的值

#### 3.2 HIGH (4个) - 重要功能修复

**问题3: 无重评分端点**
- **文件**: `app/training/api/v1/writing_endpoints.py` (缺失)
- **问题**: 无法重新评分已提交的作文
- **修复**: 添加POST /submissions/{id}/regrade端点
- **代码实现**:
```python
@router.post("/submissions/{submission_id}/regrade")
async def regrade_submission(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    service = WritingService(db)
    submission = await service.get_submission(submission_id)
    if not submission or submission.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    await service.regrade_submission(submission_id)
    return {"message": "Regrading started"}
```
- **验证标准**: ✅ 调用regrade后，submission分数更新

**问题4: AI反馈字段未填充**
- **文件**: `app/training/services/writing_service.py:255-310`
- **问题**: _grade_essay()未填充grammar_errors, vocabulary_suggestions, structure_analysis
- **修复**: 在_parse_grading_result()中解析这些字段并赋值
- **代码实现**:
```python
# In _parse_grading_result()
submission.grammar_errors = grading_result.get("grammar_errors", [])
submission.vocabulary_suggestions = grading_result.get("vocabulary_suggestions", [])
submission.structure_analysis = grading_result.get("structure_analysis", "")
```
- **验证标准**: ✅ 评分后，这些字段有值

**问题5: get_user_statistics有重复代码**
- **文件**: `app/training/services/writing_service.py:582-669`
- **问题**:  Lines 651-669重复了582-650的逻辑
- **修复**: 删除重复代码lines 651-669
- **验证标准**: ✅ 代码行数减少，功能不变

**问题6: score_level枚举值可能不匹配**
- **文件**: `app/training/services/writing_service.py:345-370`
- **问题**: AI返回的score_level与枚举值可能不匹配
- **修复**: 在_parse_grading_result()中标准化score_level
- **代码实现**:
```python
# Map AI response to enum values
score_level_map = {
    "excellent": WritingScoreLevel.EXCELLENT,
    "good": WritingScoreLevel.GOOD,
    "fair": WritingScoreLevel.FAIR,
    "poor": WritingScoreLevel.POOR
}
submission.score_level = score_level_map.get(grading_result["score_level"], WritingScoreLevel.FAIR)
```
- **验证标准**: ✅ 所有score_level值都在枚举范围内

#### 3.3 MEDIUM (2个) - 优化改进

**问题7: 添加评分结果缓存**
- **文件**: `app/training/services/writing_service.py:255-310`
- **问题**: 同一作文重复评分，每次都调用AI
- **修复**: 添加缓存，相同文本+任务不重复调用AI
- **实现**: 使用Redis缓存，key为hash(text + task_id)

**问题8: 添加评分历史记录**
- **文件**: `app/training/services/writing_service.py` (缺失)
- **问题**: 无评分历史，无法追踪评分变化
- **修复**: 创建WritingGradingHistory表，记录每次评分
- **实现**: 在_grade_essay()后插入历史记录

---

### 模块4: 听力训练 (22个问题)

#### 4.1 CRITICAL (3个) - 必须立即修复

**问题1: type_question_mapping重复定义**
- **文件**: `app/training/api/v1/listening_endpoints.py:48-59`
- **问题**: 两个字典定义，第二个覆盖第一个
- **修复**: 删除第一个定义，保留第二个
- **代码实现**:
```python
# Delete lines 48-53 (first definition)
# Keep only lines 54-59 (second definition)
```
- **验证标准**: ✅ 代码无重复，功能正常

**问题2: valid_types与实际类型不一致**
- **文件**: `app/training/api/v1/listening_endpoints.py:39, 54-59`
- **问题**: valid_types包含"passage"，但实际使用"short_passage"
- **修复**: 统一valid_types和type_question_mapping的键
- **代码实现**:
```python
# Line 39: Change
valid_types = ["short_conversation", "long_conversation", "passage", "lecture"]
# To
valid_types = ["short_conversation", "long_conversation", "short_passage", "lecture"]
```
- **验证标准**: ✅ 所有类型在valid和mapping中都存在

**问题3: Schema与Model验证不一致**
- **文件**: `app/training/schemas/listening_schemas.py:32`, `app/training/models/listening_models.py:21-28`
- **问题**: Schema允许"passage"，Model定义为"short_passage"
- **修复**: 统一枚举值为"short_passage"
- **实现**: 修改schemas.py:32，将"passage"改为"short_passage"

#### 4.2 HIGH (7个) - 重要功能修复

**问题4: 播放设置未保存到数据库**
- **文件**: `app/training/api/v1/listening_endpoints.py:362-414`
- **问题**: 播放设置只返回，不保存
- **修复**: 创建ListeningSettings表，保存用户设置
- **实现**: 
```python
# Create model
class ListeningSettings(BaseModel):
    __tablename__ = "listening_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exercise_id = Column(Integer, ForeignKey("listening_exercises.id"))
    playback_speed = Column(Float, default=1.0)
    repeat_count = Column(Integer, default=1)
    show_subtitles = Column(Boolean, default=False)
```

**问题5: 听写练习未保存**
- **文件**: `app/training/api/v1/listening_endpoints.py:417-462`
- **问题**: 听写练习数据不持久化
- **修复**: 创建DictationExercise表，保存练习数据
- **实现**: 类似问题4，创建表并保存

**问题6: 口语练习未保存**
- **文件**: `app/training/api/v1/listening_endpoints.py:465-511`
- **问题**: 口语练习数据不持久化
- **修复**: 创建SpeakingPractice表，保存练习数据
- **实现**: 类似问题4，创建表并保存

**问题7: 发音练习未保存**
- **文件**: `app/training/api/v1/listening_endpoints.py:517-578`
- **问题**: 发音练习数据不持久化
- **修复**: 创建PronunciationPractice表，保存练习数据
- **实现**: 类似问题4，创建表并保存

**问题8: 音频文件处理未实现**
- **文件**: `app/training/services/listening_service.py:97-135`
- **问题**: create_exercise()需要audio_file_id但未验证文件存在
- **修复**: 验证audio_file_id对应文件存在且可访问
- **实现**: 
```python
audio_file = await self.db.get(ListeningAudioFile, audio_file_id)
if not audio_file:
    raise ValueError(f"Audio file {audio_file_id} not found")
```

**问题9: 音频文件上传端点缺失**
- **文件**: `app/training/api/v1/listening_endpoints.py` (缺失)
- **问题**: 无法上传音频文件
- **修复**: 添加POST /listening/audio/upload端点
- **实现**: 使用FileUpload，保存到存储(本地/S3)，创建ListeningAudioFile记录

**问题10: 练习类型枚举不一致**
- **文件**: `app/training/models/listening_models.py:21-28`
- **问题**: ExerciseType枚举值与API使用的字符串不一致
- **修复**: 统一使用枚举值，避免字符串硬编码
- **实现**: 
```python
class ExerciseType(str, Enum):
    SHORT_CONVERSATION = "short_conversation"
    LONG_CONVERSATION = "long_conversation"
    SHORT_PASSAGE = "short_passage"
    LECTURE = "lecture"
```

#### 4.3 MEDIUM (8个) - 优化改进

**问题11: 添加练习难度分级**
- **文件**: `app/training/models/listening_models.py:21-28`
- **问题**: 无难度字段
- **修复**: 添加difficulty_level字段，值: ELEMENTARY, INTERMEDIATE, ADVANCED
- **实现**: `difficulty_level: Mapped[DifficultyLevel] = Column(Enum(DifficultyLevel))`

**问题12: 实现练习推荐算法**
- **文件**: `app/training/services/listening_service.py` (缺失)
- **问题**: 无个性化推荐
- **修复**: 基于用户水平、历史表现推荐练习
- **实现**: 分析用户正确率，推荐适当难度练习

**问题13: 修复练习数据统计**
- **文件**: `app/training/services/listening_service.py:326-357`
- **问题**: 统计方法简单，未考虑时间维度
- **修复**: 添加时间范围过滤，统计正确率趋势
- **实现**: 
```python
async def get_performance_trend(self, user_id: int, days: int = 30) -> list:
    # Return daily correct rate for last N days
```

**问题14: 添加练习收藏功能**
- **文件**: `app/training/models/listening_models.py` (缺失)
- **问题**: 用户无法收藏练习
- **修复**: 创建ListeningFavorite表
- **实现**: user_id + exercise_id复合主键

**问题15: 实现练习分享**
- **文件**: `app/training/api/v1/listening_endpoints.py` (缺失)
- **问题**: 无法分享练习给其他人
- **修复**: 添加分享链接生成功能
- **实现**: 生成带token的分享链接，记录分享人

**问题16: 修复练习搜索**
- **文件**: `app/training/services/listening_service.py:414-439`
- **问题**: 搜索功能简单，不支持全文搜索
- **修复**: 添加全文搜索，支持按标签、难度、类型搜索
- **实现**: 使用PostgreSQL全文搜索或Elasticsearch

**问题17: 添加练习标签**
- **文件**: `app/training/models/listening_models.py:21-28`
- **问题**: 无标签系统，无法分类练习
- **修复**: 添加tags字段，存储标签列表
- **实现**: `tags: Mapped[list[str]] = Column(JSON)`

**问题18: 实现练习批处理**
- **文件**: `app/training/services/listening_service.py` (缺失)
- **问题**: 无法批量导入/导出练习
- **修复**: 添加批量导入/导出功能
- **实现**: 支持Excel/CSV格式导入，JSON格式导出

#### 4.4 LOW (4个) - 完善性修复

**问题19: 添加练习模板**
- **文件**: `app/training/models/listening_models.py` (缺失)
- **问题**: 无法创建练习模板
- **修复**: 创建ListeningExerciseTemplate表
- **实现**: 模板包含预设问题、答案、解析

**问题20: 实现练习版本管理**
- **文件**: `app/training/models/listening_models.py` (缺失)
- **问题**: 练习修改后无法追踪历史版本
- **修复**: 添加版本控制，每次修改创建新版本
- **实现**: 添加version字段，复制旧记录创建新版本

**问题21: 修复练习导入导出**
- **文件**: `app/training/services/listening_service.py` (缺失)
- **问题**: 导入导出格式不标准
- **修复**: 使用标准格式(Excel/CSV/JSON)，包含完整元数据
- **实现**: 定义标准schema，验证导入数据

**问题22: 实现练习版本管理**
- **文件**: `app/training/models/listening_models.py` (缺失)
- **问题**: 练习修改后无法追踪历史版本
- **修复**: 添加版本控制，每次修改创建新版本
- **实现**: 添加version字段，复制旧记录创建新版本

---

### 模块5: 资源管理 (28个问题)

#### 5.1 CRITICAL (5个) - 必须立即修复

**问题1: 权限string与enum比较错误**
- **文件**: `app/resources/services/permission_service.py:54`
- **问题**: `if permission_data.permission == "class"` 比较string和enum
- **修复**: 使用enum值比较
- **代码实现**:
```python
# Before:
if permission_data.permission == "class":

# After:
if permission_data.permission.value == "class":
```
- **验证标准**: ✅ CLASS权限检查正常工作

**问题2: CLASS权限缺少实际验证**
- **文件**: `app/resources/services/permission_service.py:117-129`
- **问题**: CLASS权限检查不验证用户是否在班级中
- **修复**: 验证用户是否在resource共享的班级中
- **代码实现**:
```python
# In _check_class_access
user_classes = await self.db.execute(
    select(ClassMembership).where(
        ClassMembership.user_id == user_id,
        ClassMembership.class_id.in_(shared_class_ids)
    )
)
if not user_classes.scalar():
    raise PermissionDeniedError("用户不在共享班级中")
```

**问题3: 版本回滚未实现**
- **文件**: `app/resources/services/version_service.py:509`
- **问题**: `_apply_rollback()`只有pass
- **修复**: 实现回滚逻辑，恢复数据到目标版本
- **代码实现**:
```python
async def _apply_rollback(self, resource_type: str, resource_id: int, target_version: ResourceVersion, user_id: int) -> None:
    # 1. Get current version
    current = await self._get_current_version(resource_type, resource_id)
    
    # 2. Restore data from target_version.snapshot
    snapshot = target_version.snapshot_data
    await self._restore_resource_data(resource_type, resource_id, snapshot)
    
    # 3. Update current version pointer
    current.version = target_version.version
    await self.db.commit()
```

**问题4: _check_resource_access是空实现**
- **文件**: `app/resources/services/permission_service.py:450-460`
- **问题**: 方法只log，不实际检查
- **修复**: 实现实际权限检查逻辑
- **代码实现**:
```python
async def _check_resource_access(self, resource_type: str, resource_id: int, user_id: int) -> None:
    # Check if user is owner
    resource = await self._get_resource(resource_type, resource_id)
    if resource.created_by == user_id:
        return
    
    # Check permission settings
    permission = await self._get_permission_settings(resource_type, resource_id)
    if permission.permission_level == PermissionLevel.PUBLIC:
        return
    
    if permission.permission_level == PermissionLevel.CLASS:
        await self._check_class_access(user_id, permission.shared_class_ids)
        return
    
    raise PermissionDeniedError("无权限访问此资源")
```

**问题5: asyncio.create_task无错误处理**
- **文件**: `app/resources/services/resource_library_service.py:208, 256, 281`
- **问题**: Fire-and-forget任务，异常静默丢失
- **修复**: 使用try-except包装，记录错误日志
- **代码实现**:
```python
# Before:
asyncio.create_task(self._async_process_document(resource.id, file_path))

# After:
async def _safe_process_document(self, resource_id: int, file_path: str):
    try:
        await self._async_process_document(resource_id, file_path)
    except Exception as e:
        logger.error(f"Failed to process document {resource_id}: {e}")
        # Optionally update resource status to 'failed'

# Then:
asyncio.create_task(self._safe_process_document(resource.id, file_path))
```

#### 5.2 HIGH (9个) - 重要功能修复

**问题6: 缓存清除未实现**
- **文件**: `app/resources/services/resource_library_service.py:747-749`
- **问题**: `clear_cache()`只有pass
- **修复**: 实现缓存清除逻辑
- **代码实现**:
```python
async def clear_cache(self, library_id: int) -> None:
    cache_keys = await self.redis.keys(f"resource_library:{library_id}:*")
    for key in cache_keys:
        await self.redis.delete(key)
```

**问题7: 硬编码返回值**
- **文件**: `app/resources/services/permission_service.py:374-384`
- **问题**: `_get_course_name()`, `_get_user_name()`返回硬编码字符串
- **修复**: 实现实际数据库查询
- **代码实现**:
```python
async def _get_course_name(self, course_id: int) -> str:
    course = await self.db.get(Course, course_id)
    return course.name if course else "Unknown Course"

async def _get_user_name(self, user_id: int) -> str:
    user = await self.db.get(User, user_id)
    return user.username if user else "Unknown User"
```

**问题8: Redis连接每次请求新建**
- **文件**: `app/resources/routers/resource_router.py:61-69`
- **问题**: 每次请求创建新Redis连接
- **修复**: 使用连接池，全局共享连接
- **代码实现**:
```python
# In app/core/config.py
class Settings:
    @property
    def redis_pool(self):
        return redis.ConnectionPool.from_url(self.REDIS_URL)

# In resource_router.py
redis_client = redis.Redis(connection_pool=settings.redis_pool)
```

**问题9: 路由前缀冲突**
- **文件**: `app/resources/api/v1/permission_endpoints.py:27`, `version_endpoints.py:28`, `course_resource_endpoints.py:32`
- **问题**: 三个router都用`/api/v1/resources`前缀
- **修复**: 使用不同前缀
- **代码实现**:
```python
# permission_endpoints.py
router = APIRouter(prefix="/api/v1/resources/permissions")

# version_endpoints.py
router = APIRouter(prefix="/api/v1/resources/versions")

# course_resource_endpoints.py
router = APIRouter(prefix="/api/v1/resources/courses")
```

**问题10: 资源锁定未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无资源锁定机制，并发编辑可能冲突
- **修复**: 添加锁定机制，编辑时锁定资源
- **代码实现**:
```python
async def lock_resource(self, resource_id: int, user_id: int, timeout: int = 300) -> bool:
    lock_key = f"resource_lock:{resource_id}"
    acquired = await self.redis.set(lock_key, user_id, nx=True, ex=timeout)
    return acquired

async def unlock_resource(self, resource_id: int, user_id: int) -> bool:
    lock_key = f"resource_lock:{resource_id}"
    current_holder = await self.redis.get(lock_key)
    if current_holder == str(user_id):
        await self.redis.delete(lock_key)
        return True
    return False
```

**问题11: 资源水印未添加**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 资源无水印保护
- **修复**: 在资源上添加用户水印
- **实现**: 使用Pillow库在图片上添加文字水印，PDF使用reportlab

**问题12: 资源加密未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 敏感资源未加密
- **修复**: 对敏感资源加密存储
- **实现**: 使用Fernet对称加密，密钥存储在环境变量

**问题13: 资源元数据不完整**
- **文件**: `app/resources/services/resource_library_service.py:702-703`
- **问题**: 返回空tags和metadata
- **修复**: 从数据库加载实际tags和metadata
- **代码实现**:
```python
# In get_library_detail()
return {
    "tags": [tag.name for tag in library.tags],
    "metadata": library.metadata or {}
}
```

**问题14: 资源预览未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无资源预览功能
- **修复**: 生成资源缩略图或预览页
- **实现**: 图片自动生成缩略图，PDF生成第一页预览

#### 5.3 MEDIUM (10个) - 优化改进

**问题15: 资源评论未实现**
- **文件**: `app/resources/models/resource_models.py` (缺失)
- **问题**: 用户无法评论资源
- **修复**: 创建ResourceComment表
- **实现**: comment_id, resource_id, user_id, content, created_at

**问题16: 资源评分未实现**
- **文件**: `app/resources/models/resource_models.py` (缺失)
- **问题**: 用户无法评分资源
- **修复**: 创建ResourceRating表
- **实现**: rating_id, resource_id, user_id, rating(1-5), created_at

**问题17: 资源搜索功能弱**
- **文件**: `app/resources/services/resource_library_service.py:414-439`
- **问题**: 搜索仅支持简单like查询
- **修复**: 添加全文搜索，支持标签、分类、作者搜索
- **实现**: 使用PostgreSQL全文搜索或Elasticsearch

**问题18: 资源推荐未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无个性化推荐
- **修复**: 基于用户行为推荐相关资源
- **实现**: 使用协同过滤或内容推荐算法

**问题19: 资源统计未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无资源使用统计
- **修复**: 添加下载次数、浏览次数、收藏次数统计
- **实现**: 创建ResourceStats表，每次操作更新计数

**问题20: 资源导入功能弱**
- **文件**: `app/resources/services/resource_library_service.py:437-511`
- **问题**: 导入功能简单，不支持批量导入
- **修复**: 支持批量导入，验证数据格式
- **实现**: 支持Excel/CSV/JSON格式，验证必填字段

**问题21: 资源导出功能缺失**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无法导出资源
- **修复**: 添加导出功能，支持多种格式
- **实现**: 导出为JSON格式，包含完整元数据和内容

**问题22: 资源备份未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无备份机制
- **修复**: 定期备份资源库
- **实现**: 使用cron job定期导出，存储到S3或备份服务器

**问题23: 资源恢复未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无法从备份恢复
- **修复**: 实现从备份文件恢复
- **实现**: 读取备份文件，导入到数据库，处理冲突

**问题24: 资源审计未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无操作审计日志
- **修复**: 记录所有资源操作到审计表
- **实现**: 创建ResourceAuditLog表，记录操作类型、用户、时间、IP

#### 5.4 LOW (4个) - 完善性修复

**问题25: 资源配额未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 无用户资源配额限制
- **修复**: 添加用户资源上传配额
- **实现**: 设置每日/每月上传限制，存储使用量

**问题26: 资源同步未实现**
- **文件**: `app/resources/services/resource_library_service.py` (缺失)
- **问题**: 多实例间资源不同步
- **修复**: 使用分布式锁和消息队列同步
- **实现**: Redis锁 + RabbitMQ消息队列

**问题27: 资源标签未实现**
- **文件**: `app/resources/models/resource_models.py` (缺失)
- **问题**: 无标签系统
- **修复**: 创建ResourceTag表，支持多对多标签
- **实现**: tag_id, name, color，资源标签关联表

**问题28: 资源分类未实现**
- **文件**: `app/resources/models/resource_models.py` (缺失)
- **问题**: 无分类体系
- **修复**: 创建ResourceCategory表，支持树形分类
- **实现**: category_id, name, parent_id, level

---

## 四、修复执行顺序

### 阶段一: 基础层修复 (1-2天)
**优先级**: P0 - 阻塞所有其他修复
**问题数**: 15个
**模块**: 
- 数据库模型层 (5个)
- 配置层 (3个)
- 工具层 (7个)

**执行顺序**:
1. 修复数据库模型字段不一致 (4.14, 5.14)
2. 修复配置验证 (1.4)
3. 实现工具函数 (5.7, 5.8)
4. 添加基础索引和约束

**验证标准**: ✅ 所有基础层单元测试通过

### 阶段二: 核心功能层修复 (3-5天)
**优先级**: P0 - 核心功能不可用
**问题数**: 66个
**模块**:
- 用户认证 (18个)
- 课程管理 (20个)
- 资源管理 (28个)

**执行顺序**:
1. 修复用户认证CRITICAL问题 (1.1-1.4)
2. 修复课程管理CRITICAL问题 (2.1-2.3)
3. 修复资源管理CRITICAL问题 (5.1-5.5)
4. 修复各模块HIGH优先级问题
5. 添加核心功能集成测试

**验证标准**: ✅ 用户登录/注册/课程CRUD/资源管理100%可用

### 阶段三: 训练功能层修复 (2-3天)
**优先级**: P0 - 训练功能不可用
**问题数**: 30个
**模块**:
- 写作训练+AI批改 (8个)
- 听力训练 (22个)

**执行顺序**:
1. 修复写作训练CRITICAL问题 (3.1-3.2)
2. 修复听力训练CRITICAL问题 (4.1-4.3)
3. 修复训练功能HIGH优先级问题
4. 添加训练流程集成测试

**验证标准**: ✅ 写作提交/评分/听力练习100%可用

### 阶段四: 增强功能层修复 (2天)
**优先级**: P1 - 增强体验
**问题数**: 待审查
**模块**:
- 自适应学习
- 学习计划
- 社交学习

**验证标准**: ✅ 增强功能正常运行

### 阶段五: 完善与优化 (1天)
**优先级**: P2 - 优化完善
**问题数**: 12个LOW
**模块**:
- 性能优化
- 代码质量
- 文档完善

**验证标准**: ✅ 代码质量达标，文档完整

---

## 五、验证计划

### 每个修复后的验证步骤

1. **单元测试**: 为修复的函数添加/更新单元测试
2. **集成测试**: 测试修复功能与其他模块的交互
3. **手动测试**: 模拟用户操作，验证功能正常
4. **回归测试**: 确保修复未破坏其他功能
5. **代码审查**: 至少一名其他开发者审查代码

### 模块完成标准

**模块完成 checklist**:
- [ ] 所有CRITICAL问题修复并验证
- [ ] 所有HIGH问题修复并验证
- [ ] 90% MEDIUM问题修复并验证
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试全部通过
- [ ] 手动测试场景全部通过
- [ ] 代码审查通过
- [ ] 文档更新完成

### 整体完成标准

**系统完成 checklist**:
- [ ] 所有96个问题修复并验证
- [ ] 所有模块完成标准达成
- [ ] 端到端测试100%通过
- [ ] 性能测试达标 (响应时间<200ms)
- [ ] 安全测试通过 (无高危漏洞)
- [ ] 代码质量达标 (无CRITICAL/MAJOR问题)
- [ ] 生产环境部署验证通过
- [ ] 用户验收测试通过

---

## 六、风险与应对

### 风险1: 修复引入新问题
**应对**: 每个修复必须伴随测试，代码审查，小步提交

### 风险2: 修复时间超出预期
**应对**: 按优先级排序，先修复P0，再P1，最后P2；每日站会同步进度

### 风险3: 模块间依赖导致阻塞
**应对**: 识别依赖关系，优先修复被依赖模块；并行修复无依赖模块

### 风险4: 测试覆盖不足
**应对**: 修复同时必须添加测试，测试覆盖率作为完成标准

---

## 七、资源需求

### 人力资源
- 核心开发者: 2-3人 (全职)
- 测试工程师: 1人 (全职)
- 代码审查员: 1人 (兼职)

### 时间资源
- 总工期: 13天
- 每日工作时间: 8小时
- 加班预留: 2小时/天 (应对突发问题)

### 环境资源
- 开发环境: 1套
- 测试环境: 1套 (与生产环境配置一致)
- 生产环境: 1套 (最终部署)

---

## 八、交付物

### 代码交付物
- [ ] 修复后的完整代码库
- [ ] 单元测试代码 (覆盖率>80%)
- [ ] 集成测试代码
- [ ] 端到端测试代码

### 文档交付物
- [ ] 修复详细记录 (每个问题修复说明)
- [ ] API文档更新
- [ ] 数据库Schema文档
- [ ] 部署文档
- [ ] 运维手册

### 测试交付物
- [ ] 测试报告 (单元/集成/端到端)
- [ ] 性能测试报告
- [ ] 安全测试报告
- [ ] 用户验收测试报告

---

**计划制定**: 2026-02-27  
**计划审核**: 待审核  
**计划批准**: 待批准  
**计划版本**: v1.0  
**最后更新**: 2026-02-27 02:03:50
