# CET 项目完整重构执行计划
# 基于 Supabase + Razikus 模板

> 文档版本: 2.0
> 创建日期: 2026-03-03
> 目的: 基于 Supabase + Razikus Next.js 模板的完整重构执行计划

---

## 一、项目现状与目标

### 1.1 当前技术栈

| 层级 | 当前技术 | 备注 |
|------|----------|------|
| 前端 | React 18 + Vite + Mantine | 56+ 页面 |
| 后端 | FastAPI + SQLAlchemy | 50+ API 端点, 137 Services |
| 数据库 | PostgreSQL + Redis + Milvus | 需要迁移到 Supabase |
| AI | DeepSeek API | 保留 |
| 部署 | Docker | 迁移到 Vercel |

### 1.2 目标技术栈

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           目标架构                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  前端: Next.js 15 + React 19 + Tailwind + shadcn/ui                   │
│    └── 基于 Razikus/supabase-nextjs-template                           │
│                                                                         │
│  后端: Supabase (BaaS) + FastAPI (仅 AI)                              │
│    ├── Auth (认证/授权) ← 模板自带                                      │
│    ├── Database (PostgreSQL + pgvector)                                │
│    ├── Storage (文件/音频)                                             │
│    ├── Realtime (实时通知)                                             │
│    └── Edge Functions (业务逻辑)                                        │
│                                                                         │
│  AI 服务: 保留现有 FastAPI                                             │
│    ├── 作文批改                                                        │
│    ├── 教案生成                                                        │
│    └── 个性化推荐                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Razikus 模板结构

```
supabase-nextjs-template/
├── nextjs/                          # Next.js 15 前端 (主应用)
│   ├── src/
│   │   ├── app/                     # App Router
│   │   │   ├── (auth)/              # 认证页面 (login, register)
│   │   │   ├── (dashboard)/         # 仪表盘页面
│   │   │   ├── api/                  # API 路由
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn/ui 组件
│   │   │   └── features/             # 功能组件
│   │   ├── lib/                      # 工具函数
│   │   │   ├── supabase.ts           # Supabase 客户端
│   │   │   └── utils.ts
│   │   └── types/                    # 类型定义
│   ├── public/
│   │   └── terms/                    # 法律文档模板
│   └── .env.local                    # 环境变量
│
├── supabase/                        # Supabase 后端
│   ├── config.toml                   # Supabase 配置
│   ├── migrations/                   # 数据库迁移
│   │   └── *.sql
│   └── seed.sql                      # 种子数据
│
└── supabase-expo-template/          # React Native 移动端 (可选)
```

### 1.4 迁移范围总览

| 模块 | 功能数 | 优先级 | 迁移方式 |
|------|--------|--------|----------|
| 用户系统 | 15+ | P0 | Supabase Auth + profiles |
| 认证授权 | 10+ | P0 | 模板自带 |
| 训练中心 | 20+ | P0 | Edge Functions |
| 五大训练 | 4 | P0 | 前端 + Edge Functions |
| AI 批改 | 3 | P0 | FastAPI 保留 |
| 学习计划 | 5 | P0 | Supabase Client |
| 进度追踪 | 5 | P0 | Supabase Client |
| 错题分析 | 3 | P0 | Supabase Client |
| 课程管理 | 7+ | P1 | Supabase Client |
| 通知系统 | 2+ | P1 | Supabase Realtime |
| 数据分析 | 8+ | P2 | Supabase Client |
| 资源管理 | 6+ | P2 | Supabase Storage |

---

## 二、完整执行计划 (12周)

### 2.1 时间总览

```
Week  1  │ Week  2  │ Week  3  │ Week  4  │ Week  5  │ Week  6  │
─────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
 准备阶段  │ 基础设施   │ 核心功能   │ 核心功能   │ AI集成    │ 测试优化  │
          │           │           │           │           │           │
Week  7  │ Week  8  │ Week  9  │ Week 10  │ Week 11  │ Week 12  │
─────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
 课程模块  │ 学习功能   │ 高级功能   │ 测试优化   │ 部署上线   │ 验收交付  │
```

### 2.2 详细阶段计划

#### 📋 第一周: 准备阶段 (Week 1)

**Day 1-2: 项目初始化**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 1.1.1 | Fork Razikus 模板 | 开发者 | GitHub 仓库 |
| 1.1.2 | 安装依赖 (npm install) | 开发者 | node_modules |
| 1.1.3 | Supabase CLI 登录 | 开发者 | 已登录 CLI |
| 1.1.4 | 创建 Supabase 项目 | DBA | proj_xxx |
| 1.1.5 | 配置 .env.local | 开发者 | 环境变量 |

```bash
# 初始化命令
git clone https://github.com/Razikus/supabase-nextjs-template.git cet-project
cd cet-project
npm install

# Supabase 配置
npx supabase login
npx supabase link
npx supabase config push
npx supabase migrations up --linked
```

**Day 3-4: 数据库设计**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 1.3.1 | 分析现有 SQLAlchemy 模型 | DBA | 模型分析报告 |
| 1.3.2 | 设计 Supabase Schema | DBA | schema.sql |
| 1.3.3 | 创建迁移文件 | DBA | migrations/*.sql |
| 1.3.4 | 配置 RLS 策略 | DBA | rls-policies.sql |
| 1.3.5 | 创建 Storage Buckets | DBA | buckets 配置 |

```sql
-- supabase/migrations/001_initial_schema.sql

-- 用户扩展表 (基于模板的 profiles)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('admin', 'teacher', 'student')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 学生档案
CREATE TABLE public.student_profiles (
    id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    student_number TEXT UNIQUE,
    grade_level INTEGER,
    major TEXT,
    english_level TEXT,
    daily_study_time INTEGER DEFAULT 0,
    total_training_count INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    target_exam_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 教师档案
CREATE TABLE public.teacher_profiles (
    id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    employee_number TEXT UNIQUE,
    department TEXT,
    title TEXT,
    specialization TEXT,
    teaching_years INTEGER,
    rating DECIMAL(3,2) DEFAULT 0,
    total_students INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 训练相关表 (详见原 CET_Database_Schema_Design.md)
CREATE TABLE public.training_sessions (...);
CREATE TABLE public.questions (...);
CREATE TABLE public.training_records (...);
CREATE TABLE public.error_questions (...);
CREATE TABLE public.achievements (...);

-- RLS 策略
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);
```

**Day 5: 目录结构规划**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 1.5.1 | 创建页面目录结构 | 开发者 | 页面目录 |
| 1.5.2 | 创建组件目录结构 | 开发者 | 组件目录 |
| 1.5.3 | 创建 API 客户端 | 开发者 | API 客户端 |
| 1.5.4 | 迁移 TypeScript 类型 | 开发者 | types/ 目录 |

```
nextjs/src/
├── app/
│   ├── (auth)/                    # 认证页面 (继承模板)
│   │   ├── login/
│   │   ├── register/
│   │   └── verify/
│   ├── (dashboard)/               # 仪表盘
│   │   ├── layout.tsx
│   │   ├── page.tsx              # 首页/仪表盘
│   │   ├── student/              # 学生页面
│   │   │   ├── training/         # 训练中心
│   │   │   ├── progress/         # 学习进度
│   │   │   ├── error-book/       # 错题本
│   │   │   └── learning-plan/   # 学习计划
│   │   ├── teacher/              # 教师页面
│   │   │   ├── courses/          # 课程管理
│   │   │   ├── lesson-plan/      # 教案
│   │   │   └── analytics/        # 学习分析
│   │   └── admin/                # 管理员页面
│   │       ├── users/            # 用户管理
│   │       └── courses/          # 课程管理
│   └── api/                      # API 路由
│       └── ai/                   # AI 代理
├── components/
│   ├── ui/                       # shadcn/ui (继承)
│   ├── features/                 # 业务组件
│   │   ├── training/             # 训练相关
│   │   ├── courses/              # 课程相关
│   │   └── common/               # 通用组件
│   └── layouts/                  # 布局组件
├── lib/
│   ├── supabase/                 # Supabase 客户端
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── types.ts
│   ├── api/                      # API 客户端
│   │   ├── training.ts
│   │   ├── courses.ts
│   │   └── ai.ts
│   └── utils/
├── hooks/                        # 自定义 Hooks
│   ├── useTraining.ts
│   ├── useAuth.ts
│   └── useRealtime.ts
├── stores/                       # 状态管理 (Zustand)
│   └── userStore.ts
└── types/                        # 类型定义
    ├── user.ts
    ├── training.ts
    └── course.ts
```

---

#### 🔧 第二周: 基础设施 (Week 2)

**Day 1-2: 认证系统**

| 任务 | 内容 | 状态 |
|------|------|------|
| 2.1.1 | 配置 Supabase Auth | ⬜ 模板自带 |
| 2.1.2 | 登录页面适配 | ⬜ |
| 2.1.3 | 注册页面适配 | ⬜ |
| 2.1.4 | 密码重置流程 | ⬜ |
| 2.1.5 | 邮箱验证 | ⬜ |
| 2.1.6 | MFA 配置 (可选) | ⬜ 模板支持 |

```typescript
// nextjs/src/lib/supabase/client.ts (模板已有，验证即可)
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}

// 使用示例
const supabase = createClient()
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})
```

**Day 3-4: 用户系统**

| 任务 | 内容 | 状态 |
|------|------|------|
| 2.3.1 | profiles 表 CRUD | ⬜ |
| 2.3.2 | student_profiles 迁移 | ⬜ |
| 2.3.3 | teacher_profiles 迁移 | ⬜ |
| 2.3.4 | 权限系统 (RLS) | ⬜ |
| 2.3.5 | 用户管理页面 | ⬜ |

```typescript
// 用户资料管理
export const profileService = {
  async getProfile(userId: string) {
    const { data, error } = await supabase
      .from('profiles')
      .select('*, student_profiles(*), teacher_profiles(*)')
      .eq('id', userId)
      .single()
    return { data, error }
  },

  async updateProfile(userId: string, updates: ProfileUpdate) {
    const { data, error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('id', userId)
      .select()
      .single()
    return { data, error }
  }
}
```

**Day 5: 环境配置**

| 任务 | 内容 | 状态 |
|------|------|------|
| 2.5.1 | .env.local 配置 | ⬜ |
| 2.5.2 | .env.production 模板 | ⬜ |
| 2.5.3 | 环境变量验证脚本 | ⬜ |

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
PRIVATE_SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...

# AI 服务
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_API_BASE_URL=https://api.deepseek.com

# 应用配置
NEXT_PUBLIC_APP_NAME=CET 英语学习系统
NEXT_PUBLIC_THEME=theme-sass
```

---

#### ⚡ 第三周: 核心功能 - 训练后端 (Week 3)

**Day 1: 题目管理**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 3.1.1 | questions 表 | DBA | 迁移 SQL |
| 3.1.2 | 题目 Seed 数据 | DBA | seed.sql |
| 3.1.3 | 题目 CRUD Edge Function | 后端 | Edge Function |

```typescript
// supabase/functions/get-questions/index.ts
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
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_ANON_KEY')!
    )

    // 验证用户
    const authHeader = req.headers.get('Authorization')!
    const token = authHeader.replace('Bearer ', '')
    const { data: { user } } = await supabase.auth.getUser(token)

    if (!user) {
      throw new Error('Unauthorized')
    }

    const { type, difficulty, count } = await req.json()

    // 获取题目
    let query = supabase
      .from('questions')
      .select('*')
      .eq('is_active', true)

    if (type) query = query.eq('training_type', type)
    if (difficulty) query = query.eq('difficulty_level', difficulty)
    
    const { data: questions, error } = await query.limit(count || 10)

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

**Day 2-3: 训练会话**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 3.2.1 | training_sessions 表 | DBA | 迁移 SQL |
| 3.2.2 | 创建训练会话 | 后端 | Edge Function |
| 3.2.3 | 提交训练答案 | 后端 | Edge Function |
| 3.2.4 | 完成训练会话 | 后端 | Edge Function |

```typescript
// supabase/functions/submit-answer/index.ts
// 提交答案并记录
export const submitAnswer = async (
  sessionId: string,
  questionId: string,
  userAnswer: string,
  timeSpent: number
) => {
  // 1. 获取题目详情
  const { data: question } = await supabase
    .from('questions')
    .select('*')
    .eq('id', questionId)
    .single()

  // 2. 判断答案正确性
  const isCorrect = userAnswer === question.correct_answer

  // 3. 插入训练记录
  const { data: record } = await supabase
    .from('training_records')
    .insert({
      session_id: sessionId,
      question_id: questionId,
      user_id: user.id,
      user_answer: userAnswer,
      is_correct: isCorrect,
      time_spent: timeSpent,
      score: isCorrect ? question.max_score : 0
    })
    .select()
    .single()

  // 4. 如果错误，加入错题本
  if (!isCorrect) {
    await supabase.from('error_questions').insert({
      user_id: user.id,
      question_id: questionId,
      training_session_id: sessionId,
      user_answer: userAnswer,
      correct_answer: question.correct_answer,
      next_review_at: calculateNextReview(1) // 艾宾浩斯
    })
  }

  return { isCorrect, record }
}
```

**Day 4-5: 进度追踪**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 3.4.1 | 学习统计 Edge Function | 后端 | Edge Function |
| 3.4.2 | 成就系统 | 后端 | Edge Function + 前端 |
| 3.4.3 | 错题本 Edge Function | 后端 | Edge Function |

```typescript
// supabase/functions/get-learning-stats/index.ts
export const getLearningStats = async (userId: string) => {
  // 获取训练统计
  const { data: sessions } = await supabase
    .from('training_sessions')
    .select('*')
    .eq('user_id', userId)
    .eq('status', 'completed')

  // 计算统计数据
  const totalSessions = sessions?.length || 0
  const totalTimeSpent = sessions?.reduce((sum, s) => sum + (s.time_spent || 0), 0) || 0
  const totalQuestions = sessions?.reduce((sum, s) => sum + (s.total_questions || 0), 0) || 0
  const correctCount = sessions?.reduce((sum, s) => sum + (s.correct_count || 0), 0) || 0
  const accuracyRate = totalQuestions > 0 ? (correctCount / totalQuestions) * 100 : 0

  // 计算连续学习天数
  const { data: profile } = await supabase
    .from('student_profiles')
    .select('current_streak, longest_streak')
    .eq('id', userId)
    .single()

  return {
    total_sessions: totalSessions,
    total_time_spent: totalTimeSpent,
    total_questions: totalQuestions,
    accuracy_rate: accuracyRate.toFixed(1),
    current_streak: profile?.current_streak || 0,
    longest_streak: profile?.longest_streak || 0
  }
}
```

---

#### 🎨 第四周: 核心功能 - 训练前端 (Week 4)

**Day 1: 训练中心页面**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 4.1.1 | 训练中心主页面 | 前端 | page.tsx |
| 4.1.2 | 训练类型选择 | 前端 | 组件 |
| 4.1.3 | 难度选择器 | 前端 | 组件 |

**Day 2-3: 题目展示组件**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 4.2.1 | 选择题组件 | 前端 | MultipleChoice.tsx |
| 4.2.2 | 填空题组件 | 前端 | FillBlank.tsx |
| 4.2.3 | 听力播放器 | 前端 | AudioPlayer.tsx |
| 4.2.4 | 写作编辑器 | 前端 | WritingEditor.tsx |

**Day 4-5: 结果展示**

| 任务 | 内容 | 负责人 | 交付物 |
|------|------|--------|--------|
| 4.4.1 | 答题结果页 | 前端 | page.tsx |
| 4.4.2 | 进度条组件 | 前端 | ProgressBar.tsx |
| 4.4.3 | AI 反馈展示 | 前端 | AIFeedback.tsx |
| 4.4.4 | 成就解锁动画 | 前端 | Confetti.tsx |

```typescript
// nextjs/src/app/(dashboard)/student/training/page.tsx
'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { TrainingTypeSelector } from '@/components/features/training/TypeSelector'
import { QuestionCard } from '@/components/features/training/QuestionCard'
import { ProgressBar } from '@/components/features/training/ProgressBar'

export default function TrainingCenter() {
  const supabase = createClient()
  const [session, setSession] = useState<TrainingSession | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)

  const startTraining = async (type: string, difficulty: number) => {
    // 创建训练会话
    const { data: newSession } = await supabase
      .from('training_sessions')
      .insert({
        training_type: type,
        difficulty_level: difficulty,
        status: 'in_progress'
      })
      .select()
      .single()

    // 获取题目
    const { data: questions } = await supabase.functions.invoke('get-questions', {
      body: { type, difficulty, count: 10 }
    })

    setSession(newSession)
    setQuestions(questions.questions)
  }

  const submitAnswer = async (answer: string) => {
    const currentQuestion = questions[currentIndex]
    const { data } = await supabase.functions.invoke('submit-answer', {
      body: {
        session_id: session.id,
        question_id: currentQuestion.id,
        user_answer: answer,
        time_spent: 30
      }
    })

    // 显示结果
    if (data.isCorrect) {
      // 显示正确反馈
    } else {
      // 显示错误反馈
    }
  }

  return (
    <div className="container mx-auto p-4">
      {session ? (
        <>
          <ProgressBar current={currentIndex + 1} total={questions.length} />
          <QuestionCard
            question={questions[currentIndex]}
            onSubmit={submitAnswer}
          />
        </>
      ) : (
        <TrainingTypeSelector onStart={startTraining} />
      )}
    </div>
  )
}
```

---

#### 📚 第五周: 五大训练模块 (Week 5)

**Day 1: 词汇训练**

| 任务 | 内容 | 页面 |
|------|------|------|
| 5.1.1 | 单词选择题 | vocabulary/page.tsx |
| 5.1.2 | 单词拼写 | spelling/page.tsx |
| 5.1.3 | 记忆曲线复习 | review/page.tsx |

**Day 2: 听力训练**

| 任务 | 内容 | 页面 |
|------|------|------|
| 5.2.1 | 听力选择题 | listening/page.tsx |
| 5.2.2 | 音频播放器组件 | AudioPlayer.tsx |
| 5.2.3 | 听力进度追踪 | progress/page.tsx |

**Day 3: 阅读训练**

| 任务 | 内容 | 页面 |
|------|------|------|
| 5.3.1 | 阅读理解 | reading/page.tsx |
| 5.3.2 | 段落匹配 | matching/page.tsx |
| 5.3.3 | 词汇推断 | inference/page.tsx |

**Day 4: 写作训练**

| 任务 | 内容 | 页面 |
|------|------|------|
| 5.4.1 | 写作练习 | writing/page.tsx |
| 5.4.2 | AI 批改集成 | grading/page.tsx |
| 5.4.3 | 写作模板 | templates/page.tsx |

**Day 5: 自适应学习**

| 任务 | 内容 | 页面 |
|------|------|------|
| 5.5.1 | 难度调整算法 | adaptive/page.tsx |
| 5.5.2 | 个性化推荐 | recommendations/page.tsx |
| 5.5.3 | 学习报告 | report/page.tsx |

```typescript
// 自适应难度算法
export const calculateAdaptiveDifficulty = async (userId: string, type: string) => {
  // 获取最近 10 次答题记录
  const { data: recentRecords } = await supabase
    .from('training_records')
    .select('is_correct, difficulty_level')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(10)

  // 计算正确率
  const correctCount = recentRecords?.filter(r => r.is_correct).length || 0
  const accuracyRate = correctCount / (recentRecords?.length || 1)

  // 难度调整
  let newDifficulty = 3 // 默认中等
  if (accuracyRate >= 0.8) newDifficulty = Math.min(5, currentDifficulty + 1)
  else if (accuracyRate < 0.6) newDifficulty = Math.max(1, currentDifficulty - 1)

  return newDifficulty
}
```

---

#### 🤖 第六周: AI 集成 (Week 6)

**Day 1-2: FastAPI AI 服务准备**

| 任务 | 内容 | 负责人 |
|------|------|--------|
| 6.1.1 | 保留现有 FastAPI | 后端 |
| 6.1.2 | API 文档整理 | 后端 |
| 6.1.3 | 错误处理统一 | 后端 |

```python
# 现有 FastAPI 保留，位置: /api/v1/ai/
# 作文批改
POST /api/v1/ai/grading
# 教案生成
POST /api/v1/ai/lesson-plan
# 个性化推荐
POST /api/v1/ai/recommendation
```

**Day 3-4: Edge Function 代理**

| 任务 | 内容 | 负责人 |
|------|------|--------|
| 6.3.1 | AI 批改代理 | 后端 |
| 6.3.2 | 请求限流 | 后端 |
| 6.3.3 | 错误处理 | 后端 |

```typescript
// supabase/functions/ai-grading/index.ts
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const DEEPSEEK_API_KEY = Deno.env.get('DEEPSEEK_API_KEY')!
const FASTAPI_URL = Deno.env.get('FASTAPI_URL') || 'http://localhost:8000'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!
  )

  // 验证用户
  const authHeader = req.headers.get('Authorization')!
  const { data: { user } } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''))
  
  if (!user) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 })
  }

  const { content, type, question_id } = await req.json()

  // 调用 FastAPI
  const response = await fetch(`${FASTAPI_URL}/api/v1/ai/grading`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content,
      type,
      question_id,
      user_id: user.id
    })
  })

  const result = await response.json()

  // 保存批改结果
  if (result.id) {
    await supabase.from('grading_results').insert({
      user_id: user.id,
      question_id,
      submission_text: content,
      overall_score: result.overall_score,
      detailed_scores: result.detailed_scores,
      feedback: result.feedback,
      ai_model: result.ai_model,
      status: 'completed'
    })
  }

  return new Response(JSON.stringify(result), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

**Day 5: 前端集成**

| 任务 | 内容 | 负责人 |
|------|------|--------|
| 6.5.1 | AI 服务客户端 | 前端 |
| 6.5.2 | 批改结果展示 | 前端 |
| 6.5.3 | 加载状态处理 | 前端 |

---

#### 📋 第七周: 课程模块 (Week 7)

**Day 1-2: 课程管理**

| 任务 | 内容 | 页面 |
|------|------|------|
| 7.1.1 | 课程列表 | admin/courses/page.tsx |
| 7.1.2 | 课程详情 | courses/[id]/page.tsx |
| 7.1.3 | 课程创建/编辑 | courses/edit/page.tsx |

**Day 3-4: 班级管理**

| 任务 | 内容 | 页面 |
|------|------|------|
| 7.2.1 | 班级列表 | admin/classes/page.tsx |
| 7.2.2 | 学生分配 | classes/[id]/page.tsx |
| 7.2.3 | 课程安排 | schedule/page.tsx |

**Day 5: 作业管理**

| 任务 | 内容 | 页面 |
|------|------|------|
| 7.3.1 | 作业列表 | assignments/page.tsx |
| 7.3.2 | 作业提交 | assignments/[id]/page.tsx |
| 7.3.3 | 作业批改 | grading/page.tsx |

---

#### 📊 第八周: 学习功能 (Week 8)

**Day 1: 学习计划**

| 任务 | 内容 | 页面 |
|------|------|------|
| 8.1.1 | 计划创建 | learning-plan/create/page.tsx |
| 8.1.2 | 计划追踪 | learning-plan/page.tsx |
| 8.1.3 | AI 建议 | learning-plan/ai-suggestions/page.tsx |

**Day 2: 进度追踪**

| 任务 | 内容 | 页面 |
|------|------|------|
| 8.2.1 | 进度仪表盘 | progress/page.tsx |
| 8.2.2 | 统计图表 | progress/charts/page.tsx |
| 8.2.3 | 周报生成 | progress/weekly/page.tsx |

**Day 3: 错题本**

| 任务 | 内容 | 页面 |
|------|------|------|
| 8.3.1 | 错题列表 | error-book/page.tsx |
| 8.3.2 | 错题复习 | error-book/review/page.tsx |
| 8.3.3 | 艾宾浩斯提醒 | error-book/reminder/page.tsx |

**Day 4: 成就系统**

| 任务 | 内容 | 页面 |
|------|------|------|
| 8.4.1 | 成就列表 | achievements/page.tsx |
| 8.4.2 | 成就解锁 | achievements/unlock/page.tsx |
| 8.4.3 | 排行榜 | leaderboard/page.tsx |

**Day 5: 教师功能**

| 任务 | 内容 | 页面 |
|------|------|------|
| 8.5.1 | 教案生成 | teacher/lesson-plan/page.tsx |
| 8.5.2 | 学习分析 | teacher/analytics/page.tsx |
| 8.5.3 | 教学调整 | teacher/adjustments/page.tsx |

---

#### 🚀 第九周: 高级功能 (Week 9)

**Day 1-2: 通知系统**

| 任务 | 内容 | 实现 |
|------|------|------|
| 9.1.1 | 实时通知 | Supabase Realtime |
| 9.1.2 | 通知列表 | 页面 |
| 9.1.3 | 推送设置 | 页面 |

```typescript
// 实时通知订阅
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
        // 显示通知
        showToast(payload.new)
        // 更新 badge
        updateBadge()
      }
    )
    .subscribe()

  return channel
}
```

**Day 3-4: 资源管理**

| 任务 | 内容 | 实现 |
|------|------|------|
| 9.3.1 | 文件上传 | Supabase Storage |
| 9.3.2 | 音频管理 | Storage + Audio |
| 9.3.3 | 词汇库 | 页面 + 数据库 |

**Day 5: 社交功能 (可选 P2)**

| 任务 | 内容 | 实现 |
|------|------|------|
| 9.5.1 | 学习小组 | 页面 |
| 9.5.2 | 讨论区 | 页面 |
| 9.5.3 | 分享功能 | 页面 |

---

#### ✅ 第十周: 测试优化 (Week 10)

**Day 1-2: 单元测试**

```bash
# 测试框架: Vitest + React Testing Library
npm install -D vitest @testing-library/react @testing-library/jest-dom

# 运行测试
npm run test
npm run test:coverage
```

| 测试内容 | 覆盖率目标 |
|----------|------------|
| 组件测试 | 70% |
| Hook 测试 | 80% |
| 工具函数测试 | 90% |
| Edge Functions | 80% |

**Day 3-4: 集成测试**

```typescript
// 集成测试示例
describe('Training Flow', () => {
  it('should complete training session', async () => {
    // 1. 登录
    const { user } = await signInAsStudent()
    
    // 2. 开始训练
    const { session } = await startTraining(user.id, 'vocabulary', 3)
    
    // 3. 提交答案
    const { isCorrect } = await submitAnswer(session.id, question.id, 'a')
    
    // 4. 验证结果
    expect(isCorrect).toBe(true)
  })
})
```

**Day 5: E2E 测试**

```bash
# 使用 Playwright
npm init playwright@latest

# 运行 E2E
npm run test:e2e
```

---

#### 📦 第十一周: 部署上线 (Week 11)

**Day 1-2: Vercel 部署**

```bash
# 1. Vercel 项目创建
# 通过 GitHub OAuth 授权
# 选择仓库
# 配置环境变量

# 2. 环境变量配置 (Vercel Dashboard)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx
PRIVATE_SUPABASE_SERVICE_KEY=eyJxxx
DEEPSEEK_API_KEY=sk-xxx
```

**Day 3: Supabase 生产环境**

```bash
# 1. 生产数据库配置
# Project Settings → Database

# 2. 运行迁移
npx supabase db push

# 3. 配置 RLS (生产环境)
# 确保所有表都有 RLS 策略

# 4. Storage Bucket 配置
# 生产环境的 bucket 设置
```

**Day 4: 域名配置**

| 任务 | 内容 |
|------|------|
| 4.1 | Vercel 域名绑定 |
| 4.2 | Supabase URL 白名单 |
| 4.3 | HTTPS 证书 |
| 4.4 | CDN 配置 |

**Day 5: 上线验证**

| 验证项 | 内容 |
|--------|------|
| 功能测试 | 核心流程跑通 |
| 性能测试 | 首屏 < 2s |
| 安全测试 | RLS 验证 |
| 监控验证 | Sentry 连接 |

---

#### 🎯 第十二周: 验收交付 (Week 12)

**Day 1-2: 验收测试**

| 模块 | 验收标准 |
|------|----------|
| 用户系统 | 注册/登录/登出正常 |
| 训练中心 | 题目获取/提交/完成正常 |
| 五大训练 | 全部功能正常 |
| AI 批改 | 批改结果返回正常 |
| 课程管理 | CRUD 正常 |
| 通知系统 | 实时通知正常 |

**Day 3-4: 文档交付**

| 文档 | 内容 |
|------|------|
| API 文档 | 所有 Edge Functions |
| 部署文档 | 部署步骤 |
| 使用手册 | 用户指南 |
| 维护手册 | 运维指南 |

**Day 5: 项目交付**

| 交付物 | 内容 |
|--------|------|
| 源代码 | GitHub 仓库 |
| 线上地址 | 生产 URL |
| 文档 | Confluence/Notion |
| 培训 | 使用培训 |

---

## 三、里程碑

### 3.1 关键里程碑

| 里程碑 | 完成条件 | 目标日期 |
|--------|----------|----------|
| M1: 项目启动 | 模板 Fork + 本地运行 | Week 1 Day 2 |
| M2: 认证完成 | 登录/注册可用 | Week 2 Day 5 |
| M3: 用户系统 | CRUD + 权限 | Week 3 Day 5 |
| M4: 训练核心 | 题目获取 + 提交 | Week 4 Day 5 |
| M5: 五大训练 | 全部上线 | Week 5 Day 5 |
| M6: AI 集成 | 批改可用 | Week 6 Day 5 |
| M7: 课程模块 | 完整上线 | Week 7 Day 5 |
| M8: 学习功能 | 完整上线 | Week 8 Day 5 |
| M9: 测试通过 | 全部测试通过 | Week 10 Day 5 |
| M10: 上线 | 生产环境可用 | Week 11 Day 5 |
| M11: 验收 | 客户验收通过 | Week 12 Day 5 |

### 3.2 每周检查点

```
每周五: 进度检查 + 下周计划
- 代码完成度
- 测试覆盖率
- 阻塞问题
- 风险评估
```

---

## 四、任务分解

### 4.1 前端任务 (224小时)

| 任务 | 时间 | 依赖 |
|------|------|------|
| 项目初始化 | 4h | - |
| 目录结构 | 8h | - |
| Auth 页面适配 | 16h | Supabase Auth |
| Admin 页面 (15个) | 40h | Auth + API |
| Teacher 页面 (19个) | 48h | Auth + API |
| Student 页面 (17个) | 40h | Auth + API |
| 组件重构 | 24h | shadcn/ui |
| API 客户端 | 16h | Edge Functions |
| 状态管理 | 8h | - |
| 样式适配 | 24h | Tailwind |

### 4.2 后端任务 (98小时)

| 任务 | 时间 | 依赖 |
|------|------|------|
| Supabase 项目创建 | 2h | - |
| Database Schema | 8h | - |
| RLS 策略 | 8h | Schema |
| Storage Buckets | 4h | - |
| Edge Functions (基础) | 16h | Schema |
| Edge Functions (训练) | 24h | Schema |
| Edge Functions (课程) | 16h | Schema |
| FastAPI AI 服务 | 16h | - |
| 部署配置 | 4h | - |

---

## 五、风险评估与应对

### 5.1 高风险

| 风险 | 影响 | 概率 | 应对 |
|------|------|------|------|
| 数据迁移丢失 | 高 | 低 | 充分测试 + 多次备份 |
| 性能问题 | 高 | 中 | 提前做性能测试 |
| 第三方依赖 | 高 | 中 | 准备备用方案 |

### 5.2 中风险

| 风险 | 影响 | 概率 | 应对 |
|------|------|------|------|
| 需求变更 | 中 | 高 | 敏捷迭代 |
| RLS 配置错误 | 中 | 中 | 充分测试 |
| 缓存策略 | 中 | 中 | 设计评审 |

### 5.3 低风险

| 风险 | 影响 | 概率 | 应对 |
|------|------|------|------|
| 第三方服务不可用 | 低 | 低 | 备用服务 |

---

## 六、回滚方案

### 6.1 回滚触发条件

| 条件 | 说明 |
|------|------|
| 严重 Bug | 影响核心功能 |
| 性能下降 | 响应时间 > 3s |
| 数据丢失 | 无法恢复 |

### 6.2 回滚步骤

```
1. 停止新系统流量
2. 切换回旧系统 DNS
3. 验证旧系统功能
4. 分析问题原因
5. 修复后重新上线
```

### 6.3 数据备份

| 类型 | 频率 | 保留 |
|------|------|------|
| 数据库 | 每日 | 30天 |
| 文件 | 每周 | 90天 |
| 配置 | 每次变更 | 永久 |

---

## 七、团队分工

### 7.1 角色

| 角色 | 人数 | 职责 |
|------|------|------|
| 前端开发 | 2 | 前端页面 + 组件 |
| 后端开发 | 1 | Edge Functions + FastAPI |
| DBA | 1 | Schema + RLS + 性能 |
| 测试 | 1 | 测试 + QA |
| PM | 1 | 项目管理 |

### 7.2 每日站会

| 时间 | 内容 |
|------|------|
| 10:00 | 昨日完成 / 今日计划 / 阻碍 |

---

## 八、验收标准

### 8.1 功能验收

| 功能 | 验收标准 |
|------|----------|
| 登录/注册 | 邮箱注册、登录、登出正常 |
| 用户管理 | CRUD + 权限控制正常 |
| 训练中心 | 题目获取、提交、完成正常 |
| 五大训练 | 词汇/听力/阅读/写作/自适应正常 |
| AI 批改 | 作文提交后返回批改结果 |
| 课程管理 | 课程列表、详情、注册正常 |
| 通知 | 实时通知正常接收 |

### 8.2 性能验收

| 指标 | 标准 |
|------|------|
| 首屏加载 | < 2s |
| API 响应 | < 500ms |
| 并发支持 | 1000+ 用户 |

### 8.3 安全验收

| 检查项 | 标准 |
|--------|------|
| RLS | 未授权无法访问数据 |
| XSS | 无 XSS 漏洞 |
| CSRF | CSRF 保护正常 |

---

## 九、环境变量清单

### 9.1 开发环境 (.env.local)

```bash
# Supabase (本地)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx
PRIVATE_SUPABASE_SERVICE_KEY=eyJxxx

# AI 服务
DEEPSEEK_API_KEY=sk-dev
DEEPSEEK_API_BASE_URL=http://localhost:8000

# 应用
NEXT_PUBLIC_APP_NAME=CET 英语学习系统
NEXT_PUBLIC_THEME=theme-sass
APP_ENV=development
DEBUG=true
```

### 9.2 生产环境 (.env.production)

```bash
# Supabase (生产)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx
PRIVATE_SUPABASE_SERVICE_KEY=eyJxxx

# AI 服务
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_API_BASE_URL=https://api.deepseek.com

# 应用
NEXT_PUBLIC_APP_NAME=CET 英语学习系统
NEXT_PUBLIC_APP_URL=https://your-domain.com
NEXT_PUBLIC_THEME=theme-sass
APP_ENV=production
```

---

## 十、模板适配清单

### 10.1 需要修改的模板文件

| 文件 | 修改内容 |
|------|----------|
| `app/(auth)/login/page.tsx` | 适配 CET 登录流程 |
| `app/(auth)/register/page.tsx` | 适配 CET 注册流程 |
| `app/(dashboard)/page.tsx` | 改为 CET 仪表盘 |
| `components/ui/` | 添加 CET 业务组件 |
| `lib/supabase/types.ts` | 添加 CET 类型定义 |
| `public/terms/` | 替换法律文档 |

### 10.2 需要删除的模板内容

| 内容 | 说明 |
|------|------|
| `app/(dashboard)/tasks/` | 示例任务管理 |
| `components/features/demo/` | 示例组件 |
| `seed.sql` | 替换为 CET 种子数据 |

---

## 附录

### A. 资源链接

- [Supabase 文档](https://supabase.com/docs)
- [Next.js 文档](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Razikus 模板](https://github.com/razikus/supabase-nextjs-template)
- [Vercel 部署](https://vercel.com/docs)

### B. 技术栈版本

| 技术 | 版本 |
|------|------|
| Node.js | ≥18.x |
| Next.js | 15.x |
| React | 19.x |
| Supabase | Latest |
| TypeScript | ≥5.x |
| Tailwind CSS | ≥3.x |

---

**文档结束**
