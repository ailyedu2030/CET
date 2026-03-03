# CET 项目数据库 Schema 设计文档

> 文档版本: 1.0  
> 创建日期: 2026-03-03  
> 目的: 为迁移到 Supabase 提供详细的数据库 Schema 映射

---

## 一、核心枚举类型

### 1.1 用户类型 (UserType)

| 值 | 说明 | 迁移到 Supabase |
|---|------|-----------------|
| `admin` | 管理员 | users.role = 'admin' |
| `teacher` | 教师 | users.role = 'teacher' |
| `student` | 学生 | users.role = 'student' |

### 1.2 训练类型 (TrainingType)

| 值 | 说明 |
|---|------|
| `vocabulary` | 词汇训练 |
| `listening` | 听力训练 |
| `reading` | 阅读训练 |
| `writing` | 写作训练 |
| `translation` | 翻译训练 |
| `grammar` | 语法训练 |
| `comprehensive` | 综合训练 |

### 1.3 难度等级 (DifficultyLevel)

| 值 | 说明 |
|---|------|
| 1 | 初级 (BEGINNER) |
| 2 | 基础 (ELEMENTARY) |
| 3 | 中级 (INTERMEDIATE) |
| 4 | 中高级 (UPPER_INTERMEDIATE) |
| 5 | 高级 (ADVANCED) |

### 1.4 题目类型 (QuestionType)

| 值 | 说明 |
|---|------|
| `multiple_choice` | 选择题 |
| `fill_blank` | 填空题 |
| `true_false` | 判断题 |
| `short_answer` | 简答题 |
| `essay` | 作文题 |
| `listening_comprehension` | 听力理解 |
| `reading_comprehension` | 阅读理解 |
| `translation_en_to_cn` | 英译中 |
| `translation_cn_to_en` | 中译英 |

### 1.5 批改状态 (GradingStatus)

| 值 | 说明 |
|---|------|
| `pending` | 待批改 |
| `grading` | 批改中 |
| `completed` | 已完成 |
| `failed` | 批改失败 |
| `reviewing` | 人工复审中 |

---

## 二、用户模块 (users)

### 2.1 用户表 (users)

```sql
-- 基础用户表 (Supabase auth.users 扩展)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('admin', 'teacher', 'student')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 策略
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 用户可读写自己的 profile
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- 管理员可读写所有
CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND user_type = 'admin')
    );
```

| 字段 | 类型 | 说明 | Supabase 类型 |
|------|------|------|--------------|
| id | UUID | 用户ID | uuid |
| username | TEXT | 用户名 | text |
| email | TEXT | 邮箱 | text |
| user_type | TEXT | 用户类型 | text |
| is_active | BOOLEAN | 是否激活 | boolean |
| is_verified | BOOLEAN | 是否验证 | boolean |
| last_login | TIMESTAMP | 最后登录 | timestamptz |
| created_at | TIMESTAMP | 创建时间 | timestamptz |
| updated_at | TIMESTAMP | 更新时间 | timestamptz |

### 2.2 学生档案表 (student_profiles)

```sql
CREATE TABLE public.student_profiles (
    id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    student_number TEXT UNIQUE,  -- 学号
    grade_level INTEGER,  -- 年级
    major TEXT,  -- 专业
    enrollment_date DATE,  -- 入学日期
    target_exam_date DATE,  -- 目标考试日期
    english_level TEXT,  -- 当前英语水平
    daily_study_time INTEGER,  -- 每日学习时间(分钟)
    total_study_days INTEGER,  -- 累计学习天数
    total_training_count INTEGER DEFAULT 0,  -- 训练总次数
    current_streak INTEGER DEFAULT 0,  -- 当前连续学习天数
    longest_streak INTEGER DEFAULT 0,  -- 最长连续学习天数
    avatar_url TEXT,  -- 头像URL
    bio TEXT,  -- 个人简介
    preferences JSONB DEFAULT '{}',  -- 用户偏好设置
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.3 教师档案表 (teacher_profiles)

```sql
CREATE TABLE public.teacher_profiles (
    id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    employee_number TEXT UNIQUE,  -- 工号
    department TEXT,  -- 院系
    title TEXT,  -- 职称
    specialization TEXT,  -- 专业方向
    teaching_years INTEGER,  -- 教龄
    qualifications JSONB DEFAULT '[]',  -- 资质证书
    teaching_courses JSONB DEFAULT '[]',  -- 教授课程
    availability JSONB DEFAULT '[]',  -- 可用时间段
    rating DECIMAL(3,2) DEFAULT 0,  -- 评分
    total_students INTEGER DEFAULT 0,  -- 教授学生数
    bio TEXT,  -- 个人简介
    avatar_url TEXT,  -- 头像URL
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.4 登录会话表 (login_sessions)

```sql
CREATE TABLE public.login_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    refresh_token TEXT,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.5 角色表 (roles)

```sql
CREATE TABLE public.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 默认角色
INSERT INTO public.roles (code, name, description, permissions) VALUES
('admin', '管理员', '系统管理员', '["*"]'),
('teacher', '教师', '教师用户', '["courses:read", "courses:write", "students:read"]'),
('student', '学生', '学生用户', '["training:read", "training:write"]');
```

### 2.6 权限表 (permissions)

```sql
CREATE TABLE public.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 三、训练模块 (training)

### 3.1 训练会话表 (training_sessions)

```sql
CREATE TABLE public.training_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    training_type TEXT NOT NULL,  -- vocabulary, listening, reading, writing
    difficulty_level INTEGER NOT NULL,  -- 1-5
    session_name TEXT,
    status TEXT DEFAULT 'in_progress',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    total_questions INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    score DECIMAL(5,2),
    time_spent INTEGER DEFAULT 0,  -- 花费时间(秒)
    ai_recommendations JSONB,  -- AI推荐
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 题目表 (questions)

```sql
CREATE TABLE public.questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    training_type TEXT NOT NULL,
    question_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    difficulty_level INTEGER NOT NULL,
    max_score DECIMAL(5,2) DEFAULT 10.00,
    time_limit INTEGER,  -- 时间限制(秒)
    knowledge_points JSONB DEFAULT '[]',  -- 知识点
    tags JSONB DEFAULT '[]',  -- 标签
    correct_answer TEXT NOT NULL,
    answer_analysis TEXT,  -- 答案解析
    grading_criteria JSONB,  -- 评分标准
    audio_url TEXT,  -- 听力音频URL
    image_urls JSONB DEFAULT '[]',  -- 图片URLs
    source TEXT,  -- 来源
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3 训练记录表 (training_records)

```sql
CREATE TABLE public.training_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES public.training_sessions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES public.questions(id) ON DELETE SET NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    user_answer TEXT,
    ai_evaluation JSONB,  -- AI评估结果
    score DECIMAL(5,2),
    is_correct BOOLEAN,
    time_spent INTEGER,  -- 花费时间(秒)
    difficulty_level INTEGER,
    knowledge_points JSONB DEFAULT '[]',
    error_type TEXT,  -- 错误类型
    error_analysis TEXT,  -- 错题分析
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.4 学习计划表 (learning_plans)

```sql
CREATE TABLE public.learning_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    target_date DATE,
    status TEXT DEFAULT 'active',
    daily_goals JSONB DEFAULT '[]',  -- 每日目标
    progress DECIMAL(5,2) DEFAULT 0,
    completed_items JSONB DEFAULT '[]',
    ai_suggestions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.5 错题本表 (error_questions)

```sql
CREATE TABLE public.error_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    question_id UUID REFERENCES public.questions(id) ON DELETE CASCADE,
    training_session_id UUID REFERENCES public.training_sessions(id) ON DELETE SET NULL,
    user_answer TEXT,
    correct_answer TEXT,
    error_type TEXT,
    error_analysis TEXT,
    mastery_level INTEGER DEFAULT 0,  -- 掌握程度 0-5
    review_count INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,  -- 下次复习时间(艾宾浩斯)
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.6 成就表 (achievements)

```sql
CREATE TABLE public.achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    achievement_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    icon_url TEXT,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- 成就类型
-- training_count: 训练次数成就
-- streak_days: 连续学习天数
-- perfect_score: 满分成就
-- first_submit: 首次提交
-- vocabulary_master: 词汇大师
-- listening_master: 听力大师
-- reading_master: 阅读大师
-- writing_master: 写作大师
```

---

## 四、课程模块 (courses)

### 4.1 课程表 (courses)

```sql
CREATE TABLE public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    cover_image_url TEXT,
    category TEXT,
    difficulty_level INTEGER,
    duration_hours INTEGER,
    status TEXT DEFAULT 'draft',
    teacher_id UUID REFERENCES public.profiles(id),
    enrolled_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0,
    tags JSONB DEFAULT '[]',
    syllabus JSONB,  -- 教学大纲
    price DECIMAL(10,2) DEFAULT 0,
    is_free BOOLEAN DEFAULT true,
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 班级表 (classes)

```sql
CREATE TABLE public.classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    course_id UUID REFERENCES public.courses(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES public.profiles(id),
    semester TEXT,
    year INTEGER,
    max_students INTEGER DEFAULT 50,
    current_students INTEGER DEFAULT 0,
    schedule JSONB DEFAULT '[]',  -- 课程安排
    status TEXT DEFAULT 'open',
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 班级学生表 (class_students)

```sql
CREATE TABLE public.class_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID REFERENCES public.classes(id) ON DELETE CASCADE,
    student_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'active',
    UNIQUE(class_id, student_id)
);
```

### 4.4 作业表 (assignments)

```sql
CREATE TABLE public.assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES public.courses(id) ON DELETE CASCADE,
    class_id UUID REFERENCES public.classes(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    questions JSONB DEFAULT '[]',  -- 题目列表
    total_points DECIMAL(5,2),
    due_date TIMESTAMPTZ,
    allow_late BOOLEAN DEFAULT false,
    late_deduction DECIMAL(5,2) DEFAULT 0,
    attachments JSONB DEFAULT '[]',
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 五、AI 模块 (ai)

### 5.1 批改记录表 (grading_results)

```sql
CREATE TABLE public.grading_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    training_session_id UUID REFERENCES public.training_sessions(id) ON DELETE SET NULL,
    question_id UUID REFERENCES public.questions(id) ON DELETE SET NULL,
    submission_text TEXT NOT NULL,
    ai_model TEXT,  -- 使用的AI模型
    overall_score DECIMAL(5,2),
    detailed_scores JSONB,  -- 详细评分
    strengths JSONB DEFAULT '[]',  -- 优点
    improvements JSONB DEFAULT '[]',  -- 改进建议
    feedback TEXT,
    grading_time_ms INTEGER,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 教案表 (lesson_plans)

```sql
CREATE TABLE public.lesson_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    course_id UUID REFERENCES public.courses(id) ON DELETE SET NULL,
    content JSONB NOT NULL,  -- 教案内容
    objectives JSONB DEFAULT '[]',  -- 教学目标
    duration INTEGER,  -- 时长(分钟)
    materials JSONB DEFAULT '[]',  -- 教材
    activities JSONB DEFAULT '[]',  -- 教学活动
    assessments JSONB DEFAULT '[]',  -- 评估方式
    ai_generated BOOLEAN DEFAULT false,
    status TEXT DEFAULT 'draft',
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.3 教学大纲表 (syllabi)

```sql
CREATE TABLE public.syllabi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES public.courses(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES public.profiles(id),
    title TEXT NOT NULL,
    content JSONB NOT NULL,
    week_count INTEGER,
    topics JSONB DEFAULT '[]',
    objectives JSONB DEFAULT '[]',
    assessments JSONB DEFAULT '[]',
    ai_generated BOOLEAN DEFAULT false,
    status TEXT DEFAULT 'pending',
    approved_by UUID REFERENCES public.profiles(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 六、通知模块 (notifications)

### 6.1 通知表 (notifications)

```sql
CREATE TABLE public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL,  -- system, achievement, assignment, reminder
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link_url TEXT,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 七、资源模块 (resources)

### 7.1 资源表 (resources)

```sql
CREATE TABLE public.resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,  -- document, video, audio, image, link
    file_url TEXT,
    file_size INTEGER,
    mime_type TEXT,
    storage_path TEXT,
    uploaded_by UUID REFERENCES public.profiles(id),
    course_id UUID REFERENCES public.courses(id) ON DELETE SET NULL,
    tags JSONB DEFAULT '[]',
    download_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT false,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 7.2 词汇表 (vocabulary)

```sql
CREATE TABLE public.vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word TEXT NOT NULL,
    pronunciation TEXT,  -- 发音
    meaning TEXT NOT NULL,  -- 释义
    part_of_speech TEXT,  -- 词性
    examples JSONB DEFAULT '[]',  -- 例句
    synonyms JSONB DEFAULT '[]',  -- 近义词
    antonyms JSONB DEFAULT '[]',  -- 反义词
    difficulty_level INTEGER,
    frequency_rank INTEGER,  -- 词频排名
    audio_url TEXT,  -- 发音音频
    image_url TEXT,  -- 图片
    et cetera JSONB DEFAULT '[]',  -- 词根词缀
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 八、分析模块 (analytics)

### 8.1 学习分析表 (learning_analytics)

```sql
CREATE TABLE public.learning_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    training_count INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0,  -- 总学习时间(秒)
    questions_attempted INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,2),
    strength_areas JSONB DEFAULT '[]',  -- 强项领域
    weakness_areas JSONB DEFAULT '[]',  -- 弱项领域
    ai_insights JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);
```

### 8.2 系统指标表 (system_metrics)

```sql
CREATE TABLE public.system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name TEXT NOT NULL,
    metric_value DECIMAL(10,2),
    unit TEXT,
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 指标类型
-- cpu_usage: CPU使用率
-- memory_usage: 内存使用率
-- disk_usage: 磁盘使用率
-- active_users: 活跃用户数
-- api_calls: API调用次数
-- response_time: 响应时间
-- error_rate: 错误率
```

---

## 九、向量搜索 (pgvector)

### 9.1 题目向量表

```sql
-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 题目向量表
CREATE TABLE public.question_embeddings (
    id UUID PRIMARY KEY REFERENCES public.questions(id) ON DELETE CASCADE,
    embedding vector(1536),  -- DeepSeek embedding 维度
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建向量索引
CREATE INDEX ON public.question_embeddings USING ivfflat (embedding vector_cosine_ops);

-- 语义搜索函数
CREATE OR REPLACE FUNCTION match_questions(
    query_embedding vector(1536),
    match_count INT DEFAULT 5
) RETURNS TABLE (
    id UUID,
    similarity FLOAT
) LANGUAGE SQL AS $$
    SELECT id, 1 - (embedding <=> query_embedding) AS similarity
    FROM question_embeddings
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
```

---

## 十、Supabase Storage

### 10.1 Bucket 配置

```sql
-- 创建存储 Bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('avatars', 'avatars', true, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp']),
    ('course-covers', 'course-covers', true, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp']),
    ('audio', 'audio', true, 52428800, ARRAY['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg']),
    ('documents', 'documents', true, 104857600, ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']),
    ('private', 'private', false, 104857600, NULL);
```

---

## 十一、Realtime 配置

### 11.1 实时通知

```sql
-- 启用 Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;
ALTER PUBLICATION supabase_realtime ADD TABLE public.training_sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE public.achievements;
```

---

## 十二、迁移检查清单

### 12.1 表结构迁移

| 表名 | 状态 | 备注 |
|------|------|------|
| profiles | ⬜ | 扩展 auth.users |
| student_profiles | ⬜ | |
| teacher_profiles | ⬜ | |
| login_sessions | ⬜ | |
| roles | ⬜ | |
| permissions | ⬜ | |
| training_sessions | ⬜ | |
| questions | ⬜ | |
| training_records | ⬜ | |
| learning_plans | ⬜ | |
| error_questions | ⬜ | |
| achievements | ⬜ | |
| courses | ⬜ | |
| classes | ⬜ | |
| class_students | ⬜ | |
| assignments | ⬜ | |
| grading_results | ⬜ | |
| lesson_plans | ⬜ | |
| syllabi | ⬜ | |
| notifications | ⬜ | |
| resources | ⬜ | |
| vocabulary | ⬜ | |
| learning_analytics | ⬜ | |
| system_metrics | ⬜ | |
| question_embeddings | ⬜ | pgvector |

### 12.2 RLS 策略

| 表名 | 策略数 | 状态 |
|------|--------|------|
| profiles | 3 | ⬜ |
| training_sessions | 2 | ⬜ |
| questions | 1 | ⬜ |
| courses | 2 | ⬜ |

---

## 附录：Supabase SQL 参考

### A.1 基础查询示例

```sql
-- 获取用户学习进度
SELECT 
    p.username,
    p.user_type,
    COUNT(ts.id) as total_sessions,
    SUM(ts.total_questions) as total_questions,
    COALESCE(AVG(ts.score), 0) as avg_score
FROM public.profiles p
LEFT JOIN public.training_sessions ts ON p.id = ts.user_id
WHERE p.user_type = 'student'
GROUP BY p.id, p.username, p.user_type;

-- 获取错题本
SELECT 
    q.*,
    eq.user_answer,
    eq.correct_answer,
    eq.error_analysis,
    eq.mastery_level
FROM public.error_questions eq
JOIN public.questions q ON eq.question_id = q.id
WHERE eq.user_id = auth.uid()
ORDER BY eq.created_at DESC;

-- 语义搜索题目
SELECT * FROM match_questions(
    (SELECT embedding FROM question_embeddings WHERE id = 'some-question-id'::uuid),
    10
) AS matched;
```

### A.2 Realtime 订阅

```typescript
// 前端订阅通知
const channel = supabase
  .channel('notifications')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'notifications',
      filter: `user_id=eq.${userId}`
    },
    (payload) => {
      console.log('New notification:', payload.new);
    }
  )
  .subscribe();
```

---

**文档结束**
