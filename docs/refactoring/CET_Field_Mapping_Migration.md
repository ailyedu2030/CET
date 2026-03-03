# CET 项目字段级数据映射与迁移文档

> 文档版本: 1.0  
> 创建日期: 2026-03-03  
> 目的: 详细记录每个旧字段到新字段的映射关系

---

## 一、用户模块字段映射

### 1.1 User (用户表)

#### 旧版 (SQLAlchemy)
```python
# 位置: app/users/models/user_models.py
class User(BaseModel):
    username: Mapped[str]          # String(50), unique, index
    email: Mapped[str]            # String(100), unique, index
    password_hash: Mapped[str]    # String(255)
    user_type: Mapped[UserType]   # Enum(UserType)
    is_active: Mapped[bool]       # Boolean, default=True
    is_verified: Mapped[bool]     # Boolean, default=False
    last_login: Mapped[datetime | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

#### 新版 (Supabase)
```sql
-- 使用 Supabase auth.users + public.profiles
-- auth.users: id, email, encrypted_password, created_at, email_confirmed_at
-- public.profiles: 扩展用户信息
```

#### 字段映射表

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `users.id` | `auth.users.id` | UUID 自动生成 | Supabase 管理 |
| `users.username` | `public.profiles.username` | 直接迁移 | |
| `users.email` | `auth.users.email` | 直接迁移 | |
| `users.password_hash` | `auth.users.encrypted_password` | ⚠️ 需重新加密 | Supabase 使用 bcrypt |
| `users.user_type` | `public.profiles.user_type` | 直接迁移 | 转为 text |
| `users.is_active` | `public.profiles.is_active` | 直接迁移 | |
| `users.is_verified` | `auth.users.email_confirmed_at` | 时间戳判断 | 有值=已验证 |
| `users.last_login` | `public.profiles.last_login` | 直接迁移 | |
| `users.created_at` | `auth.users.created_at` | 直接迁移 | |
| `users.updated_at` | `public.profiles.updated_at` | 直接迁移 | |

#### 迁移脚本

```sql
-- Step 1: 创建临时表存储用户数据（不包含密码）
CREATE TABLE temp_users AS
SELECT 
    username,
    email,
    user_type::text as user_type,
    is_active,
    is_verified,
    last_login,
    created_at,
    updated_at
FROM old_users;

-- Step 2: 导出为 CSV（包含密码哈希）
COPY old_users(id, username, password_hash) 
TO '/tmp/users_password.csv' 
WITH (FORMAT CSV);

-- Step 3: 密码处理（需要用户重新设置密码）
-- Supabase 使用不同的加密方式，无法直接迁移密码
-- 方案: 重置密码链接
```

---

### 1.2 StudentProfile (学生档案)

#### 字段映射表

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `student_profiles.user_id` | `student_profiles.id` | UUID 关联 | FK → profiles.id |
| `student_profiles.student_number` | `student_profiles.student_number` | 直接迁移 | |
| `student_profiles.grade_level` | `student_profiles.grade_level` | 直接迁移 | int |
| `student_profiles.major` | `student_profiles.major` | 直接迁移 | |
| `student_profiles.enrollment_date` | `student_profiles.enrollment_date` | 直接迁移 | date |
| `student_profiles.target_exam_date` | `student_profiles.target_exam_date` | 直接迁移 | date |
| `student_profiles.english_level` | `student_profiles.english_level` | 直接迁移 | |
| `student_profiles.daily_study_time` | `student_profiles.daily_study_time` | 直接迁移 | int (分钟) |
| `student_profiles.total_study_days` | `student_profiles.total_study_days` | 直接迁移 | int |
| `student_profiles.total_training_count` | `student_profiles.total_training_count` | 直接迁移 | int |
| `student_profiles.current_streak` | `student_profiles.current_streak` | 直接迁移 | int |
| `student_profiles.longest_streak` | `student_profiles.longest_streak` | 直接迁移 | int |
| `student_profiles.avatar_url` | `student_profiles.avatar_url` | 文件迁移 | 需迁移到 Supabase Storage |
| `student_profiles.bio` | `student_profiles.bio` | 直接迁移 | |
| `student_profiles.preferences` | `student_profiles.preferences` | JSON 迁移 | |

---

### 1.3 TeacherProfile (教师档案)

#### 字段映射表

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `teacher_profiles.user_id` | `teacher_profiles.id` | UUID 关联 | FK → profiles.id |
| `teacher_profiles.employee_number` | `teacher_profiles.employee_number` | 直接迁移 | |
| `teacher_profiles.department` | `teacher_profiles.department` | 直接迁移 | |
| `teacher_profiles.title` | `teacher_profiles.title` | 直接迁移 | |
| `teacher_profiles.specialization` | `teacher_profiles.specialization` | 直接迁移 | |
| `teacher_profiles.teaching_years` | `teacher_profiles.teaching_years` | 直接迁移 | int |
| `teacher_profiles.qualifications` | `teacher_profiles.qualifications` | JSON 迁移 | |
| `teacher_profiles.teaching_courses` | `teacher_profiles.teaching_courses` | JSON 迁移 | |
| `teacher_profiles.availability` | `teacher_profiles.availability` | JSON 迁移 | |
| `teacher_profiles.rating` | `teacher_profiles.rating` | 直接迁移 | decimal |
| `teacher_profiles.total_students` | `teacher_profiles.total_students` | 直接迁移 | int |
| `teacher_profiles.bio` | `teacher_profiles.bio` | 直接迁移 | |
| `teacher_profiles.avatar_url` | `teacher_profiles.avatar_url` | 文件迁移 | 需迁移到 Storage |

---

### 1.4 LoginSession (登录会话)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `login_sessions.id` | `login_sessions.id` | UUID | 自动生成 |
| `login_sessions.user_id` | `login_sessions.user_id` | UUID 关联 | |
| `login_sessions.session_token` | - | ⚠️ 不迁移 | Supabase 管理 Session |
| `login_sessions.refresh_token` | - | ⚠️ 不迁移 | Supabase 管理 |
| `login_sessions.ip_address` | `login_sessions.ip_address` | 直接迁移 | |
| `login_sessions.user_agent` | `login_sessions.user_agent` | 直接迁移 | |
| `login_sessions.is_active` | - | ⚠️ 不迁移 | Supabase 管理 |
| `login_sessions.last_activity` | - | ⚠️ 不迁移 | Supabase 管理 |
| `login_sessions.expires_at` | - | ⚠️ 不迁移 | Supabase 管理 |

---

## 二、训练模块字段映射

### 2.1 TrainingSession (训练会话)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `training_sessions.id` | `training_sessions.id` | UUID 自动生成 | |
| `training_sessions.user_id` | `training_sessions.user_id` | UUID 关联 | profiles.id |
| `training_sessions.training_type` | `training_sessions.training_type` | text 迁移 | |
| `training_sessions.difficulty_level` | `training_sessions.difficulty_level` | int 迁移 | 1-5 |
| `training_sessions.session_name` | `training_sessions.session_name` | text 迁移 | |
| `training_sessions.status` | `training_sessions.status` | text 迁移 | in_progress/completed |
| `training_sessions.started_at` | `training_sessions.started_at` | timestamptz | |
| `training_sessions.completed_at` | `training_sessions.completed_at` | timestamptz | nullable |
| `training_sessions.total_questions` | `training_sessions.total_questions` | int | |
| `training_sessions.correct_count` | `training_sessions.correct_count` | int | |
| `training_sessions.score` | `training_sessions.score` | decimal | |
| `training_sessions.time_spent` | `training_sessions.time_spent` | int (秒) | |
| `training_sessions.ai_recommendations` | `training_sessions.ai_recommendations` | JSON | |
| `training_sessions.metadata` | `training_sessions.metadata` | JSON | |

---

### 2.2 Question (题目)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `questions.id` | `questions.id` | UUID 自动生成 | |
| `questions.training_type` | `questions.training_type` | text 迁移 | |
| `questions.question_type` | `questions.question_type` | text 迁移 | |
| `questions.title` | `questions.title` | text 迁移 | |
| `questions.content` | `questions.content` | text 迁移 | |
| `questions.difficulty_level` | `questions.difficulty_level` | int 迁移 | |
| `questions.max_score` | `questions.max_score` | decimal | |
| `questions.time_limit` | `questions.time_limit` | int (秒) | nullable |
| `questions.knowledge_points` | `questions.knowledge_points` | JSON 数组 | |
| `questions.tags` | `questions.tags` | JSON 数组 | |
| `questions.correct_answer` | `questions.correct_answer` | text | |
| `questions.answer_analysis` | `questions.answer_analysis` | text | nullable |
| `questions.grading_criteria` | `questions.grading_criteria` | JSON | |
| `questions.audio_url` | `questions.audio_url` | 文件 URL | 需迁移到 Storage |
| `questions.image_urls` | `questions.image_urls` | JSON 数组 | 需迁移到 Storage |
| `questions.source` | `questions.source` | text | |
| `questions.usage_count` | `questions.usage_count` | int | |
| `questions.success_rate` | `questions.success_rate` | decimal | |
| `questions.is_active` | `questions.is_active` | boolean | |

---

### 2.3 TrainingRecord (训练记录)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `training_records.id` | `training_records.id` | UUID 自动生成 | |
| `training_records.session_id` | `training_records.session_id` | UUID 关联 | training_sessions.id |
| `training_records.question_id` | `training_records.question_id` | UUID 关联 | questions.id |
| `training_records.user_id` | `training_records.user_id` | UUID 关联 | profiles.id |
| `training_records.user_answer` | `training_records.user_answer` | text | |
| `training_records.ai_evaluation` | `training_records.ai_evaluation` | JSON | |
| `training_records.score` | `training_records.score` | decimal | |
| `training_records.is_correct` | `training_records.is_correct` | boolean | |
| `training_records.time_spent` | `training_records.time_spent` | int (秒) | |
| `training_records.difficulty_level` | `training_records.difficulty_level` | int | |
| `training_records.knowledge_points` | `training_records.knowledge_points` | JSON | |
| `training_records.error_type` | `training_records.error_type` | text | nullable |
| `training_records.error_analysis` | `training_records.error_analysis` | text | nullable |

---

### 2.4 LearningPlan (学习计划)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `learning_plans.id` | `learning_plans.id` | UUID 自动生成 | |
| `learning_plans.user_id` | `learning_plans.user_id` | UUID 关联 | profiles.id |
| `learning_plans.title` | `learning_plans.title` | text | |
| `learning_plans.description` | `learning_plans.description` | text | nullable |
| `learning_plans.target_date` | `learning_plans.target_date` | date | nullable |
| `learning_plans.status` | `learning_plans.status` | text | |
| `learning_plans.daily_goals` | `learning_plans.daily_goals` | JSON 数组 | |
| `learning_plans.progress` | `learning_plans.progress` | decimal | 0-100 |
| `learning_plans.completed_items` | `learning_plans.completed_items` | JSON 数组 | |
| `learning_plans.ai_suggestions` | `learning_plans.ai_suggestions` | JSON | |

---

### 2.5 ErrorQuestion (错题本)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `error_questions.id` | `error_questions.id` | UUID 自动生成 | |
| `error_questions.user_id` | `error_questions.user_id` | UUID 关联 | profiles.id |
| `error_questions.question_id` | `error_questions.question_id` | UUID 关联 | questions.id |
| `error_questions.session_id` | `error_questions.training_session_id` | UUID 关联 | training_sessions.id |
| `error_questions.user_answer` | `error_questions.user_answer` | text | |
| `error_questions.correct_answer` | `error_questions.correct_answer` | text | |
| `error_questions.error_type` | `error_questions.error_type` | text | nullable |
| `error_questions.error_analysis` | `error_questions.error_analysis` | text | nullable |
| `error_questions.mastery_level` | `error_questions.mastery_level` | int 0-5 | |
| `error_questions.review_count` | `error_questions.review_count` | int | |
| `error_questions.last_reviewed_at` | `error_questions.last_reviewed_at` | timestamptz | nullable |
| `error_questions.next_review_at` | `error_questions.next_review_at` | timestamptz | nullable (艾宾浩斯) |

---

## 三、课程模块字段映射

### 3.1 Course (课程)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `courses.id` | `courses.id` | UUID 自动生成 | |
| `courses.title` | `courses.title` | text | |
| `courses.description` | `courses.description` | text | nullable |
| `courses.cover_image_url` | `courses.cover_image_url` | 文件 URL | 需迁移到 Storage |
| `courses.category` | `courses.category` | text | |
| `courses.difficulty_level` | `courses.difficulty_level` | int | nullable |
| `courses.duration_hours` | `courses.duration_hours` | int | |
| `courses.status` | `courses.status` | text | draft/published |
| `courses.teacher_id` | `courses.teacher_id` | UUID 关联 | profiles.id |
| `courses.enrolled_count` | `courses.enrolled_count` | int | |
| `courses.rating` | `courses.rating` | decimal | |
| `courses.tags` | `courses.tags` | JSON 数组 | |
| `courses.syllabus` | `courses.syllabus` | JSON | |
| `courses.price` | `courses.price` | decimal | |
| `courses.is_free` | `courses.is_free` | boolean | |
| `courses.is_published` | `courses.is_published` | boolean | |
| `courses.published_at` | `courses.published_at` | timestamptz | nullable |

---

### 3.2 Class (班级)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `classes.id` | `classes.id` | UUID 自动生成 | |
| `classes.name` | `classes.name` | text | |
| `classes.course_id` | `classes.course_id` | UUID 关联 | courses.id |
| `classes.teacher_id` | `classes.teacher_id` | UUID 关联 | profiles.id |
| `classes.semester` | `classes.semester` | text | nullable |
| `classes.year` | `classes.year` | int | nullable |
| `classes.max_students` | `classes.max_students` | int | |
| `classes.current_students` | `classes.current_students` | int | |
| `classes.schedule` | `classes.schedule` | JSON 数组 | |
| `classes.status` | `classes.status` | text | open/closed |
| `classes.start_date` | `classes.start_date` | date | nullable |
| `classes.end_date` | `classes.end_date` | date | nullable |

---

### 3.3 Assignment (作业)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `assignments.id` | `assignments.id` | UUID 自动生成 | |
| `assignments.course_id` | `assignments.course_id` | UUID 关联 | courses.id |
| `assignments.class_id` | `assignments.class_id` | UUID 关联 | classes.id |
| `assignments.title` | `assignments.title` | text | |
| `assignments.description` | `assignments.description` | text | nullable |
| `assignments.questions` | `assignments.questions` | JSON 数组 | |
| `assignments.total_points` | `assignments.total_points` | decimal | |
| `assignments.due_date` | `assignments.due_date` | timestamptz | nullable |
| `assignments.allow_late` | `assignments.allow_late` | boolean | |
| `assignments.late_deduction` | `assignments.late_deduction` | decimal | |
| `assignments.attachments` | `assignments.attachments` | JSON 数组 | 文件 URL |
| `assignments.created_by` | `assignments.created_by` | UUID 关联 | profiles.id |

---

## 四、AI 模块字段映射

### 4.1 GradingResult (批改结果)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `grading_results.id` | `grading_results.id` | UUID 自动生成 | |
| `grading_results.user_id` | `grading_results.user_id` | UUID 关联 | profiles.id |
| `grading_results.session_id` | `grading_results.training_session_id` | UUID 关联 | training_sessions.id |
| `grading_results.question_id` | `grading_results.question_id` | UUID 关联 | questions.id |
| `grading_results.submission_text` | `grading_results.submission_text` | text | |
| `grading_results.ai_model` | `grading_results.ai_model` | text | |
| `grading_results.overall_score` | `grading_results.overall_score` | decimal | |
| `grading_results.detailed_scores` | `grading_results.detailed_scores` | JSON | |
| `grading_results.strengths` | `grading_results.strengths` | JSON 数组 | |
| `grading_results.improvements` | `grading_results.improvements` | JSON 数组 | |
| `grading_results.feedback` | `grading_results.feedback` | text | |
| `grading_results.grading_time_ms` | `grading_results.grading_time_ms` | int | |
| `grading_results.status` | `grading_results.status` | text | |

---

### 4.2 LessonPlan (教案)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `lesson_plans.id` | `lesson_plans.id` | UUID 自动生成 | |
| `lesson_plans.teacher_id` | `lesson_plans.teacher_id` | UUID 关联 | profiles.id |
| `lesson_plans.title` | `lesson_plans.title` | text | |
| `lesson_plans.course_id` | `lesson_plans.course_id` | UUID 关联 | courses.id |
| `lesson_plans.content` | `lesson_plans.content` | JSON | |
| `lesson_plans.objectives` | `lesson_plans.objectives` | JSON 数组 | |
| `lesson_plans.duration` | `lesson_plans.duration` | int (分钟) | |
| `lesson_plans.materials` | `lesson_plans.materials` | JSON 数组 | |
| `lesson_plans.activities` | `lesson_plans.activities` | JSON 数组 | |
| `lesson_plans.assessments` | `lesson_plans.assessments` | JSON 数组 | |
| `lesson_plans.ai_generated` | `lesson_plans.ai_generated` | boolean | |
| `lesson_plans.status` | `lesson_plans.status` | text | draft/published |

---

## 五、通知模块字段映射

### 5.1 Notification (通知)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `notifications.id` | `notifications.id` | UUID 自动生成 | |
| `notifications.user_id` | `notifications.user_id` | UUID 关联 | profiles.id |
| `notifications.type` | `notifications.type` | text | |
| `notifications.title` | `notifications.title` | text | |
| `notifications.message` | `notifications.message` | text | |
| `notifications.link_url` | `notifications.link_url` | text | nullable |
| `notifications.is_read` | `notifications.is_read` | boolean | |
| `notifications.read_at` | `notifications.read_at` | timestamptz | nullable |
| `notifications.metadata` | `notifications.metadata` | JSON | |

---

## 六、资源模块字段映射

### 6.1 Resource (资源)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `resources.id` | `resources.id` | UUID 自动生成 | |
| `resources.title` | `resources.title` | text | |
| `resources.description` | `resources.description` | text | nullable |
| `resources.type` | `resources.type` | text | document/video/audio |
| `resources.file_url` | `resources.file_url` | 文件 URL | 需迁移到 Storage |
| `resources.file_size` | `resources.file_size` | int (字节) | |
| `resources.mime_type` | `resources.mime_type` | text | |
| `resources.storage_path` | `resources.storage_path` | text | Supabase Storage 路径 |
| `resources.uploaded_by` | `resources.uploaded_by` | UUID 关联 | profiles.id |
| `resources.course_id` | `resources.course_id` | UUID 关联 | courses.id |
| `resources.tags` | `resources.tags` | JSON 数组 | |
| `resources.download_count` | `resources.download_count` | int | |
| `resources.is_public` | `resources.is_public` | boolean | |
| `resources.status` | `resources.status` | text | |

---

### 6.2 Vocabulary (词汇)

| 旧字段 | 新字段 | 映射方式 | 说明 |
|--------|--------|---------|------|
| `vocabulary.id` | `vocabulary.id` | UUID 自动生成 | |
| `vocabulary.word` | `vocabulary.word` | text | |
| `vocabulary.pronunciation` | `vocabulary.pronunciation` | text | nullable |
| `vocabulary.meaning` | `vocabulary.meaning` | text | |
| `vocabulary.part_of_speech` | `vocabulary.part_of_speech` | text | nullable |
| `vocabulary.examples` | `vocabulary.examples` | JSON 数组 | |
| `vocabulary.synonyms` | `vocabulary.synonyms` | JSON 数组 | |
| `vocabulary.antonyms` | `vocabulary.antonyms` | JSON 数组 | |
| `vocabulary.difficulty_level` | `vocabulary.difficulty_level` | int | 1-5 |
| `vocabulary.frequency_rank` | `vocabulary.frequency_rank` | int | nullable |
| `vocabulary.audio_url` | `vocabulary.audio_url` | 文件 URL | 需迁移到 Storage |
| `vocabulary.image_url` | `vocabulary.image_url` | 文件 URL | 需迁移到 Storage |
| `vocabulary.etymology` | `vocabulary.etymology` | JSON | 词根词缀 |

---

## 七、迁移检查清单

### 7.1 直接迁移 (可以直接迁移的字段)

| 模块 | 字段数 | 状态 |
|------|--------|------|
| User | 8 | ⬜ |
| StudentProfile | 15 | ⬜ |
| TeacherProfile | 13 | ⬜ |
| TrainingSession | 14 | ⬜ |
| Question | 19 | ⬜ |
| Course | 16 | ⬜ |

### 7.2 需要处理的迁移 (需要额外处理)

| 类型 | 模块 | 处理方式 |
|------|------|---------|
| 密码 | User | 用户重置密码 |
| 文件 | 所有文件字段 | 迁移到 Supabase Storage |
| Session | LoginSession | 不迁移，使用 Supabase 管理 |
| 向量 | Question | 使用 pgvector 重新生成 |

---

**文档结束**
