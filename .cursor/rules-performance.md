# 性能优化和缓存策略规范

## ⚡ 实时响应性能要求

### 关键性能指标

- **API 响应时间**：P95 < 800ms，P99 < 2s
- **数据库查询**：单次查询 < 100ms，复杂查询 < 500ms
- **AI 服务调用**：批改 < 3s，辅助功能 < 1s，题目生成 < 2s
- **前端渲染**：首屏加载 < 2s，页面切换 < 500ms
- **并发支持**：1000+学生并发，500+教师并发

### 流式处理性能

- **流式批改**：首字节时间 < 500ms，流式间隔 < 200ms
- **实时通信**：WebSocket 消息延迟 < 100ms
- **进度更新**：学习进度实时更新，延迟 < 200ms
- **状态同步**：跨模块状态同步 < 500ms

## 🗄️ 多层缓存策略

### L1 本地缓存（应用层）

- **缓存内容**：热点 API 响应、计算结果、配置信息
- **缓存时间**：5-30 分钟，根据数据更新频率调整
- **命中率目标**：> 60%
- **实现方式**：FastAPI-Cache 装饰器、内存缓存

```python
# 本地缓存示例
from functools import lru_cache
from fastapi_cache import cache

@cache(expire=300)  # 5分钟缓存
async def get_user_profile(user_id: int):
    return await db.get_user(user_id)

@lru_cache(maxsize=1000)
def calculate_score(answers: tuple):
    # 计算密集型操作缓存
    return complex_calculation(answers)
```

### L2 Redis 缓存（分布式）

- **缓存内容**：用户会话、API 响应、向量检索结果、AI 服务结果
- **缓存时间**：1 小时-24 小时，根据业务需求
- **命中率目标**：> 30%
- **集群配置**：主从架构，读写分离

```python
# Redis缓存配置
REDIS_CACHE_CONFIG = {
    "user_sessions": {"ttl": 7200, "prefix": "session:"},
    "ai_responses": {"ttl": 3600, "prefix": "ai:"},
    "vector_search": {"ttl": 1800, "prefix": "vector:"},
    "api_responses": {"ttl": 600, "prefix": "api:"}
}
```

### L3 数据库优化

- **索引优化**：为常用查询字段建立复合索引
- **查询优化**：使用 SQLAlchemy 查询优化，避免 N+1 问题
- **连接池**：PostgreSQL 最小 10，最大 100 连接
- **读写分离**：读操作分流 70%到从库

## 🚀 异步处理架构

### 异步任务队列

- **Celery 配置**：Redis 作为消息队列和结果存储
- **任务分类**：
  - 实时任务（<1s）：用户认证、简单查询
  - 快速任务（1-5s）：AI 批改、数据分析
  - 慢任务（>5s）：报告生成、批量处理
- **优先级队列**：urgent > high > normal > low

```python
# Celery任务配置
from celery import Celery

app = Celery('cet4_learning')
app.conf.update(
    task_routes={
        'ai.tasks.grade_essay': {'queue': 'ai_fast'},
        'analytics.tasks.generate_report': {'queue': 'slow'},
        'notifications.tasks.send_email': {'queue': 'normal'},
    },
    task_annotations={
        'ai.tasks.grade_essay': {'rate_limit': '100/m'},
        'analytics.tasks.generate_report': {'rate_limit': '10/m'},
    }
)
```

### 批量处理优化

- **批量大小**：AI 请求批量 10-50 个，数据库批量 100-1000 条
- **批量间隔**：高频操作 100ms，低频操作 1s
- **处理效率**：批量处理效率提升>300%
- **错误处理**：部分失败不影响整体处理

## 📊 预计算和预加载

### 预计算机制

- **覆盖范围**：80%常用查询结果提前计算
- **计算时机**：夜间批量预计算（凌晨 2-6 点）
- **更新策略**：增量更新，避免全量重算
- **存储方式**：Redis 存储预计算结果

```python
# 预计算任务示例
@app.task
def precompute_student_analytics():
    """预计算学生分析数据"""
    students = get_active_students()
    for student in students:
        analytics_data = calculate_student_analytics(student.id)
        cache.set(f"analytics:{student.id}", analytics_data, ttl=86400)
```

### 智能预加载

- **用户行为预测**：基于历史行为预加载可能访问的内容
- **资源预加载**：前端资源懒加载和预加载
- **数据预热**：系统启动时预热热点数据
- **CDN 配置**：静态资源 CDN 缓存，命中率>90%

## 🔧 数据库性能优化

### 索引策略

```sql
-- 用户查询优化
CREATE INDEX idx_users_email_status ON users(email, status);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- 学习记录优化
CREATE INDEX idx_training_records_user_date ON training_records(user_id, created_at DESC);
CREATE INDEX idx_training_records_course ON training_records(course_id, status);

-- AI服务调用优化
CREATE INDEX idx_ai_calls_user_type ON ai_service_calls(user_id, call_type, created_at DESC);
```

### 查询优化规范

- **避免 SELECT \***：明确指定需要的字段
- **使用 LIMIT**：分页查询必须使用 LIMIT
- **JOIN 优化**：避免过多表 JOIN，考虑数据冗余
- **子查询优化**：复杂子查询改写为 JOIN

```python
# SQLAlchemy查询优化示例
# ❌ 错误方式
users = session.query(User).all()
for user in users:
    profile = session.query(UserProfile).filter_by(user_id=user.id).first()

# ✅ 正确方式
users_with_profiles = session.query(User).options(
    joinedload(User.profile)
).filter(User.status == 'active').limit(100).all()
```

## 🌐 前端性能优化

### 代码分割和懒加载

```typescript
// 路由级别代码分割
const LoginPage = lazy(() => import('@/pages/Auth/LoginPage'))
const Dashboard = lazy(() => import('@/pages/Dashboard/Dashboard'))

// 组件级别懒加载
const HeavyComponent = lazy(() => import('@/components/HeavyComponent'))

// 动态导入
const loadAnalytics = () => import('@/utils/analytics')
```

### 状态管理优化

```typescript
// Zustand状态分片
interface AppState {
  user: UserState
  courses: CoursesState
  training: TrainingState
}

// 避免不必要的重渲染
const useUserStore = create<UserState>(set => ({
  user: null,
  setUser: user => set({ user }),
}))

// 使用selector优化
const userName = useUserStore(state => state.user?.name)
```

### 网络请求优化

```typescript
// TanStack Query配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分钟
      cacheTime: 10 * 60 * 1000, // 10分钟
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// 请求去重和缓存
const useUserProfile = (userId: string) => {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUserProfile(userId),
    enabled: !!userId,
  })
}
```

## 📈 性能监控和优化

### 关键指标监控

- **响应时间**：API 响应时间分布和趋势
- **吞吐量**：每秒请求数(RPS)和并发用户数
- **错误率**：HTTP 错误率和业务错误率
- **资源使用**：CPU、内存、磁盘、网络使用率

### 性能分析工具

```python
# 性能分析装饰器
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.info(f"{func.__name__} took {duration:.3f}s")
    return wrapper

# 数据库查询监控
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # 记录慢查询
        logger.warning(f"Slow query: {total:.3f}s - {statement[:100]}")
```

## 🎯 性能优化检查清单

### 开发阶段

- [ ] API 响应时间是否<800ms
- [ ] 数据库查询是否有适当索引
- [ ] 是否使用了适当的缓存策略
- [ ] 异步任务是否正确配置
- [ ] 前端是否实现代码分割

### 测试阶段

- [ ] 负载测试是否通过
- [ ] 缓存命中率是否达标
- [ ] 并发测试是否满足要求
- [ ] 内存泄漏检查
- [ ] 性能回归测试

### 生产阶段

- [ ] 监控指标是否配置
- [ ] 告警阈值是否合理
- [ ] 性能基线是否建立
- [ ] 优化计划是否制定
- [ ] 扩容策略是否准备
