# CET 项目功能链路详解文档

> 文档版本: 1.0  
> 创建日期: 2026-03-03  
> 目的: 详细描述每个核心功能的逻辑链、数据链、功能链

---

## 一、用户认证功能链

### 1.1 用户注册流程

```
用户注册 (Register)
    │
    ├─[前端] User fills form (email, password, username, userType)
    │         ↓
    │         POST /auth/v1/signup
    │         ↓
    ├─[Supabase Auth] Create user account
    │         ├─ Generate UUID
    │         ├─ Hash password (bcrypt)
    │         ├─ Send verification email
    │         └─ Return user object
    │         ↓
    ├─[Trigger] Handle new user
    │         └─ Insert into public.profiles
    │         ↓
    ├─[RLS] Insert profile (auto with service role)
    │         ↓
    └─[前端] Show success / email verification
```

#### 数据流

| 步骤 | 数据 | 存储位置 |
|------|------|---------|
| 1 | email, password, username, userType | 前端表单 |
| 2 | POST /auth/v1/signup | Supabase Auth API |
| 3 | id (UUID), email, encrypted_password | auth.users |
| 4 | id, username, user_type | public.profiles |

---

### 1.2 用户登录流程

```
用户登录 (Login)
    │
    ├─[前端] User enters email, password
    │         ↓ POST /auth/v1/token?grant_type=password
    ├─[Supabase Auth] Verify credentials
    │         ├─ Check email exists
    │         ├─ Verify password hash
    │         ├─ Check email confirmed
    │         ├─ Generate JWT access_token
    │         └─ Generate refresh_token
    │         ↓
    ├─[获取] User profile → GET /rest/v1/profiles?id=eq.{userId}
    │         ↓
    ├─[Store] Save to localStorage/session
    │         ├─ access_token
    │         ├─ refresh_token
    │         └─ user profile
    │         ↓
    └─[前端] Redirect to dashboard
```

---

## 二、训练功能链

### 2.1 获取训练题目流程

```
获取训练题目 (Get Training Questions)
    │
    ├─[前端] User selects training type & difficulty
    │         ├─ trainingType: vocabulary/listening/reading/writing
    │         └─ difficultyLevel: 1-5
    │         ↓ POST /functions/v1/get-training-questions
    ├─[Edge Function] Verify auth
    │         ├─ Check Authorization header
    │         ├─ Decode JWT token
    │         └─ Get user_id
    │         ↓
    ├─[Query] Get questions from DB
    │         └─ SELECT * FROM questions 
    │            WHERE training_type = $1 AND difficulty_level = $2
    │         ↓
    ├─[Process] Update usage_count
    │         └─ UPDATE questions SET usage_count = usage_count + 1
    │         ↓
    └─[前端] Display questions with options
```

---

### 2.2 提交训练答案流程

```
提交训练答案 (Submit Training Answer)
    │
    ├─[前端] User submits answer
    │         ├─ session_id, question_id, user_answer, time_spent
    │         ↓ POST /functions/v1/submit-training-answer
    ├─[Edge Function] Verify & Process
    │         ├─ Get question details
    │         ├─ Compare answers (correct/incorrect)
    │         ├─ Calculate score
    │         └─ Generate AI feedback
    │         ↓
    ├─[AI Service] Get AI evaluation (optional)
    │         └─ POST /api/v1/ai/grading (FastAPI)
    │         ↓
    ├─[DB] Insert training_record
    │         └─ INSERT INTO training_records (...)
    │         ↓
    ├─[DB] Update session progress
    │         └─ UPDATE training_sessions SET ...
    │         ↓
    ├─[Check] If error → Add to error_book
    │         └─ INSERT INTO error_questions (...)
    │         ↓
    └─[前端] Show result with feedback
```

---

### 2.3 完成训练会话流程

```
完成训练会话 (Complete Training Session)
    │
    ├─[前端] User clicks "Complete"
    │         ↓ POST /functions/v1/complete-training-session
    ├─[Edge Function] Finalize session
    │         ├─ Calculate final score
    │         ├─ Calculate accuracy rate
    │         ├─ Generate summary
    │         ├─ Check achievements
    │         └─ Generate AI recommendations
    │         ↓
    ├─[DB] Update session status
    │         └─ UPDATE training_sessions SET status = 'completed'
    │         ↓
    ├─[AI] Generate learning insights
    │         └─ POST /api/v1/ai/learning-insights
    │         ↓
    ├─[Check] Unlock achievements
    │         └─ training_count >= 10 → 学习达人
    │            streak_days >= 7 → 坚持不懈
    │            perfect_score = true → 满分达人
    │         ↓
    └─[前端] Show completion summary + achievements
```

---

## 三、AI 批改功能链

### 3.1 作文批改流程

```
AI 作文批改 (AI Writing Grading)
    │
    ├─[前端] User submits writing
    │         ├─ content (作文内容), type = "writing"
    │         ↓ POST /functions/v1/ai-grading
    ├─[Edge Function] Validate & Proxy
    │         ├─ Check auth, quota
    │         └─ Forward to FastAPI
    │         ↓
    ├─[FastAPI] Process with DeepSeek
    │         ├─ Build prompt
    │         ├─ Call DeepSeek API
    │         ├─ Parse response
    │         └─ Calculate scores
    │         ↓
    ├─[Store] Save result
    │         └─ INSERT INTO grading_results
    │         ↓
    └─[前端] Display grading result
```

#### AI 评分维度

| 维度 | 权重 |
|------|------|
| grammar | 20% |
| vocabulary | 20% |
| structure | 20% |
| content | 25% |
| fluency | 15% |

---

## 四、学习进度功能链

### 4.1 进度追踪流程

```
学习进度追踪 (Progress Tracking)
    │
    ├─[数据源]
    │         ├─ training_sessions
    │         ├─ training_records
    │         └─ error_questions
    │         ↓
    ├─[Edge Function] Calculate stats
    │         ├─ Total training count
    │         ├─ Total time spent
    │         ├─ Accuracy rate
    │         └─ Streak calculation
    │         ↓
    ├─[AI] Generate insights
    │         ├─ Strengths analysis
    │         ├─ Weaknesses analysis
    │         └─ Recommendations
    │         ↓
    └─[前端] Display progress dashboard
```

---

### 4.2 错题本功能链

```
错题本 (Error Book)
    │
    ├─[触发] 答题错误 → 自动加入错题本
    │         ↓
    ├─[复习提醒] 艾宾浩斯遗忘曲线
    │         ├─ 第 1 天: 当天复习
    │         ├─ 第 3 天: 首次复习
    │         ├─ 第 7 天: 二次复习
    │         ├─ 第 14 天: 三次复习
    │         └─ 第 30 天: 四次复习
    │         ↓
    ├─[查询] GET /functions/v1/get-error-book
    │         └─ SELECT * FROM error_questions WHERE user_id = $1
    │         ↓
    ├─[复习] 强化练习 → 重新做同一类型题目
    │         ↓
    └─[更新]  mastery_level = mastery_level + 1
```

---

## 五、自适应学习功能链

### 5.1 难度调整流程

```
自适应难度调整 (Adaptive Difficulty)
    │
    ├─[分析] 用户答题表现
    │         ├─ 最近 10 次正确率
    │         ├─ 每种题型正确率
    │         ├─ 答题速度
    │         └─ 错题类型分布
    │         ↓
    ├─[算法] 计算调整
    │         ├─ 正确率 > 80%: 难度 +1
    │         ├─ 正确率 60-80%: 保持不变
    │         └─ 正确率 < 60%: 难度 -1
    │         ↓
    ├─[生成] 新推荐
    │         └─ SELECT questions WHERE difficulty = new_level
    │         ↓
    └─[前端] 展示个性化题目
```

---

## 六、通知功能链

### 6.1 实时通知流程

```
实时通知 (Real-time Notifications)
    │
    ├─[触发事件]
    │         ├─ 训练完成
    │         ├─ 获得成就
    │         ├─ 新作业
    │         └─ 系统公告
    │         ↓
    ├─[数据库] INSERT INTO notifications (...)
    │         ↓
    ├─[Supabase Realtime] WebSocket push
    │         ↓
    └─[前端] Show notification + Update badge
```

---

## 七、功能链路汇总图

### 数据流总览

```
┌────────────────────────────────────────────────────────────────┐
│                         用户层                               │
│  Admin  │  Teacher  │  Student  │  游客                   │
└────────┼────────────┼────────────┼─────────────────────────┘
         │             │            │
         ▼             ▼            ▼
┌────────────────────────────────────────────────────────────────┐
│                      API 网关层                              │
│  Supabase Client  │  Edge Functions  │  FastAPI (AI)     │
└────────┬───────────┴────────┬──────────┴────────┬─────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────────────────────────────────────────────────────┐
│                      服务层                                 │
│    Auth Service    │  Training Service  │  AI Service       │
└────────┬───────────┴────────┬──────────┴────────┬─────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────────────────────────────────────────────────────┐
│                      数据层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │   Storage    │  │   pgvector  │      │
│  │ profiles     │  │   avatars    │  │ embeddings  │      │
│  │ sessions    │  │   audio      │  └──────────────┘      │
│  │ questions    │  │   docs       │                         │
│  └──────────────┘  └──────────────┘                         │
└────────────────────────────────────────────────────────────────┘
```

---

**文档结束**
