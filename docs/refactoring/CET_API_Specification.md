# CET 项目 API 规格说明文档

> 文档版本: 1.0  
> 创建日期: 2026-03-03  
> 目的: 为迁移到 Supabase 提供详细的 API 规格说明

---

## 一、核心 API 概览

### 1.1 API 分组

| 分组 | 说明 | 迁移方式 |
|------|------|---------|
| **认证 (Auth)** | 登录、注册、Token | Supabase Auth |
| **用户 (Users)** | 用户资料、权限 | Supabase Client |
| **训练 (Training)** | 五大训练核心 | Supabase Functions |
| **AI (AI)** | 批改、推荐 | 保留 FastAPI |
| **课程 (Courses)** | 课程管理 | Supabase Client |
| **通知 (Notifications)** | 站内通知 | Supabase Realtime |

---

## 二、认证 API (Supabase Auth)

### 2.1 用户注册

```typescript
// 前端调用
const signUp = async (email: string, password: string, userData: { username: string, userType: 'student' | 'teacher' }) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: userData  // 存储额外用户信息
    }
  })
  return { data, error }
}

// Request
{
  "email": "user@example.com",
  "password": "password123",
  "options": {
    "data": {
      "username": "student001",
      "userType": "student"
    }
  }
}

// Response
{
  "user": {
    "id": "uuid-xxxx-xxxx",
    "email": "user@example.com",
    "email_confirmed_at": "2026-03-03T00:00:00Z",
    "user_metadata": {
      "username": "student001",
      "userType": "student"
    }
  },
  "session": {
    "access_token": "eyJ...",
    "refresh_token": "...",
    "expires_in": 3600
  }
}
```

### 2.2 用户登录

```typescript
// 前端调用
const signIn = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  })
  return { data, error }
}

// Request
{
  "email": "user@example.com",
  "password": "password123"
}

// Response
{
  "user": { ... },
  "session": {
    "access_token": "eyJ...",
    "refresh_token": "...",
    "expires_in": 3600,
    "expires_at": 1234567890
  }
}
```

### 2.3 Token 刷新

```typescript
// 前端调用 (Supabase 自动处理)
const { data, error } = await supabase.auth.refreshSession()

// Supabase 会自动使用 refresh_token 获取新 access_token
```

### 2.4 登出

```typescript
// 前端调用
const { error } = await supabase.auth.signOut()

// Request (无)
// Response (无 body，HTTP 200)
```

### 2.5 获取当前用户

```typescript
// 前端调用
const { data: { user }, error } = await supabase.auth.getUser()

// Response
{
  "id": "uuid-xxxx-xxxx",
  "email": "user@example.com",
  "user_metadata": {
    "username": "student001",
    "userType": "student"
  },
  "app_metadata": {
    "provider": "email",
    "providers": ["email"]
  }
}
```

---

## 三、用户资料 API

### 3.1 获取用户资料

```typescript
// 前端调用
const getProfile = async () => {
  const { data: { user } } = await supabase.auth.getUser()
  
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()
  
  return { data, error }
}

// GET /rest/v1/profiles?id=eq.{userId}

// Response
{
  "id": "uuid-xxxx-xxxx",
  "username": "student001",
  "email": "user@example.com",
  "user_type": "student",
  "is_active": true,
  "is_verified": false,
  "last_login": "2026-03-03T10:00:00Z",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-03-03T10:00:00Z"
}
```

### 3.2 更新用户资料

```typescript
// 前端调用
const updateProfile = async (updates: { username?: string, bio?: string }) => {
  const { data, error } = await supabase
    .from('profiles')
    .update(updates)
    .eq('id', userId)
    .select()
    .single()
  
  return { data, error }
}

// PATCH /rest/v1/profiles?id=eq.{userId}
// Request
{
  "username": "newUsername",
  "bio": "Hello, I'm learning English!"
}

// Response
{
  "id": "uuid-xxxx-xxxx",
  "username": "newUsername",
  "bio": "Hello, I'm learning English!",
  ...
}
```

### 3.3 获取学生档案

```typescript
// GET /rest/v1/student_profiles?profile_id=eq.{userId}

{
  "id": "uuid-xxxx-xxxx",
  "student_number": "2024001",
  "grade_level": 1,
  "major": "计算机科学",
  "english_level": "intermediate",
  "daily_study_time": 60,
  "total_training_count": 150,
  "current_streak": 7,
  "target_exam_date": "2026-06-15"
}
```

---

## 四、训练核心 API

### 4.1 获取训练题目

```typescript
// 调用 Supabase Edge Function
const getTrainingQuestions = async (type: string, difficulty: number, count: number) => {
  const { data, error } = await supabase.functions.invoke('get-training-questions', {
    body: { type, difficulty, count }
  })
  return { data, error }
}

// POST /functions/v1/get-training-questions
// Request
{
  "type": "vocabulary",
  "difficulty": 3,
  "count": 10
}

// Response
{
  "questions": [
    {
      "id": "uuid-xxxx-xxxx",
      "training_type": "vocabulary",
      "question_type": "multiple_choice",
      "title": "单词选择",
      "content": "请选择正确的翻译",
      "options": [
        { "id": "a", "text": "学习" },
        { "id": "b", "text": "工作" },
        { "id": "c", "text": "休息" },
        { "id": "d", "text": "运动" }
      ],
      "difficulty_level": 3,
      "correct_answer": "a",
      "time_limit": 30
    }
  ],
  "session_id": "uuid-xxxx-xxxx"
}
```

### 4.2 提交训练答案

```typescript
// POST /functions/v1/submit-training-answer
// Request
{
  "session_id": "uuid-xxxx-xxxx",
  "question_id": "uuid-xxxx-xxxx",
  "user_answer": "a",
  "time_spent": 25
}

// Response
{
  "is_correct": true,
  "correct_answer": "a",
  "score": 10,
  "explanation": "学习 = study",
  "ai_feedback": "回答正确！掌握良好，继续保持。"
}
```

### 4.3 完成训练会话

```typescript
// POST /functions/v1/complete-training-session
// Request
{
  "session_id": "uuid-xxxx-xxxx"
}

// Response
{
  "session": {
    "id": "uuid-xxxx-xxxx",
    "status": "completed",
    "total_questions": 10,
    "correct_count": 8,
    "score": 85.5,
    "time_spent": 600,
    "started_at": "2026-03-03T10:00:00Z",
    "completed_at": "2026-03-03T10:10:00Z"
  },
  "summary": {
    "strengths": ["词汇掌握良好", "语法理解准确"],
    "weaknesses": ["听力细节把握不足"],
    "suggestions": ["建议加强听力训练"]
  },
  "achievements_unlocked": [
    {
      "id": "ach-001",
      "title": "学习达人",
      "description": "完成10次训练"
    }
  ]
}
```

---

## 五、AI 批改 API

### 5.1 作文批改

```typescript
// 调用 FastAPI (保留现有服务)
// POST /api/v1/ai/grading

// Request
{
  "content": "In my opinion, studying English is very important...",
  "type": "writing",
  "question_id": "uuid-xxxx-xxxx",
  "user_id": "uuid-xxxx-xxxx"
}

// Response
{
  "id": "uuid-xxxx-xxxx",
  "overall_score": 85,
  "detailed_scores": {
    "grammar": 88,
    "vocabulary": 82,
    "structure": 85,
    "content": 80,
    "fluency": 90
  },
  "strengths": [
    "使用了一些高级词汇",
    "文章结构清晰"
  ],
  "improvements": [
    "建议增加更多连接词",
    "语法错误: should have done"
  ],
  "feedback": "整体写得不错，注意语法细节...",
  "ai_model": "deepseek-chat",
  "grading_time_ms": 2500
}
```

### 5.2 AI 教案生成

```typescript
// POST /api/v1/ai/lesson-plan

// Request
{
  "topic": "一般过去时",
  "level": "beginner",
  "duration": 45,
  "objectives": ["掌握规则", "能正确使用"]
}

// Response
{
  "id": "uuid-xxxx-xxxx",
  "title": "一般过去时",
  "duration": 45,
  "stages": [
    {
      "name": "导入",
      "duration": 5,
      "activities": ["展示图片", "提问过去的事情"]
    },
    {
      "name": "讲解",
      "duration": 15,
      "activities": ["讲解规则", "举例说明"]
    },
    {
      "name": "练习",
      "duration": 15,
      "activities": ["填空练习", "对话练习"]
    },
    {
      "name": "总结",
      "duration": 10,
      "activities": ["复习要点", "布置作业"]
    }
  ],
  "materials": ["PPT", "练习册"],
  "homework": "完成练习册第10页"
}
```

---

## 六、学习进度 API

### 6.1 获取学习统计

```typescript
// GET /functions/v1/get-learning-stats

// Response
{
  "user_id": "uuid-xxxx-xxxx",
  "overview": {
    "total_sessions": 150,
    "total_time_spent": 36000,  // 秒
    "total_questions": 1200,
    "accuracy_rate": 78.5,
    "current_streak": 7,
    "longest_streak": 21
  },
  "by_type": {
    "vocabulary": {
      "sessions": 50,
      "accuracy": 85,
      "level": 4
    },
    "listening": {
      "sessions": 30,
      "accuracy": 72,
      "level": 3
    },
    "reading": {
      "sessions": 40,
      "accuracy": 80,
      "level": 4
    },
    "writing": {
      "sessions": 30,
      "accuracy": 75,
      "level": 3
    }
  },
  "weekly_progress": [
    { "date": "2026-02-25", "time": 60, "accuracy": 75 },
    { "date": "2026-02-26", "time": 90, "accuracy": 80 },
    ...
  ]
}
```

### 6.2 获取错题本

```typescript
// GET /functions/v1/get-error-book

// Response
{
  "total_errors": 45,
  "mastery_levels": {
    "0": 5,    // 完全不会
    "1": 10,
    "2": 15,
    "3": 8,
    "4": 5,
    "5": 2     // 已掌握
  },
  "errors": [
    {
      "id": "uuid-xxxx-xxxx",
      "question": {
        "id": "q-001",
        "content": "The cat ___ under the table.",
        "correct_answer": "is sitting"
      },
      "user_answer": "sits",
      "error_type": "时态错误",
      "error_analysis": "应该用进行时",
      "mastery_level": 2,
      "review_count": 3,
      "next_review": "2026-03-05T00:00:00Z"
    }
  ]
}
```

---

## 七、课程 API

### 7.1 获取课程列表

```typescript
// GET /rest/v1/courses?select=*

// Response
[
  {
    "id": "uuid-xxxx-xxxx",
    "title": "CET-4 词汇精讲",
    "description": "全面讲解四级词汇",
    "cover_image_url": "https://...",
    "category": "vocabulary",
    "difficulty_level": 2,
    "duration_hours": 20,
    "teacher_id": "uuid-xxxx-xxxx",
    "enrolled_count": 150,
    "rating": 4.8,
    "is_published": true
  }
]
```

### 7.2 获取课程详情

```typescript
// GET /functions/v1/get-course-details?course_id=xxx

// Response
{
  "id": "uuid-xxxx-xxxx",
  "title": "CET-4 词汇精讲",
  "description": "全面讲解四级词汇",
  "teacher": {
    "id": "uuid-xxxx-xxxx",
    "name": "张老师",
    "title": "教授",
    "rating": 4.9
  },
  "syllabus": [
    { "week": 1, "topic": "Unit 1-2", "goals": ["掌握50个单词"] },
    { "week": 2, "topic": "Unit 3-4", "goals": ["掌握50个单词"] }
  ],
  "reviews": [
    { "user": "student001", "rating": 5, "comment": "讲得很好" }
  ],
  "is_enrolled": true
}
```

---

## 八、通知 API

### 8.1 订阅通知

```typescript
// 前端 - Realtime 订阅
const subscribeToNotifications = (userId: string) => {
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
        // 新通知到达
        showNotification(payload.new)
      }
    )
    .subscribe()
  
  return channel
}
```

### 8.2 获取通知列表

```typescript
// GET /rest/v1/notifications?user_id=eq.{userId}&order=created_at.desc

// Response
[
  {
    "id": "uuid-xxxx-xxxx",
    "type": "achievement",
    "title": "获得新成就！",
    "message": "恭喜获得'连续学习7天'成就",
    "link_url": "/achievements",
    "is_read": false,
    "created_at": "2026-03-03T10:00:00Z"
  }
]
```

---

## 九、Supabase Edge Functions

### 9.1 函数列表

| 函数名 | 说明 | 触发方式 |
|--------|------|---------|
| `get-training-questions` | 获取训练题目 | HTTP POST |
| `submit-training-answer` | 提交答案 | HTTP POST |
| `complete-training-session` | 完成训练 | HTTP POST |
| `get-learning-stats` | 学习统计 | HTTP GET |
| `get-error-book` | 错题本 | HTTP GET |
| `get-course-details` | 课程详情 | HTTP GET |
| `ai-grading` | AI批改代理 | HTTP POST |

### 9.2 Edge Function 示例

```typescript
// supabase/functions/get-training-questions/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    // 验证用户
    const authHeader = req.headers.get('Authorization')!
    const token = authHeader.replace('Bearer ', '')
    const { data: { user } } = await supabaseClient.auth.getUser(token)

    if (!user) {
      throw new Error('Unauthorized')
    }

    const { type, difficulty, count } = await req.json()

    // 从数据库获取题目
    const { data: questions, error } = await supabaseClient
      .from('questions')
      .select('*')
      .eq('training_type', type)
      .eq('difficulty_level', difficulty)
      .eq('is_active', true)
      .limit(count)

    if (error) throw error

    return new Response(JSON.stringify({ questions }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})
```

---

## 十、迁移检查清单

### 10.1 需要转换为 Edge Functions 的 API

| 原 API | 新函数 | 优先级 |
|--------|--------|--------|
| /training/center | get-training-questions | P0 |
| /training/submit | submit-training-answer | P0 |
| /training/complete | complete-training-session | P0 |
| /learning/stats | get-learning-stats | P1 |
| /error-book | get-error-book | P1 |
| /course/details | get-course-details | P1 |

### 10.2 保留 FastAPI 的 API

| 原 API | 说明 |
|--------|------|
| /ai/grading | AI批改（需要 GPU） |
| /ai/lesson-plan | 教案生成 |
| /ai/recommendation | 个性化推荐 |

---

## 附录：常见错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|---------|
| 400 | 请求参数错误 | 检查输入 |
| 401 | 未认证 | 重新登录 |
| 403 | 无权限 | 检查权限 |
| 404 | 资源不存在 | 检查 ID |
| 429 | 请求过多 | 限流等待 |
| 500 | 服务器错误 | 反馈客服 |

---

**文档结束**
