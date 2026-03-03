# CET 项目环境变量配置清单

> 文档版本: 1.0  
> 创建日期: 2026-03-03  
> 目的: 列出所有需要的环境变量及其配置说明

---

## 一、环境变量总览

| 环境 | 变量数 | 说明 |
|------|--------|------|
| 开发环境 | 20+ | 本地开发使用 |
| 测试环境 | 20+ | CI/CD 使用 |
| 生产环境 | 25+ | 正式环境使用 |

---

## 二、Supabase 环境变量

### 2.1 必需变量

| 变量名 | 说明 | 示例值 | 敏感度 |
|--------|------|--------|--------|
| `SUPABASE_URL` | Supabase 项目 URL | `https://xxx.supabase.co` | 低 |
| `SUPABASE_ANON_KEY` | 匿名访问 Key | `eyJhbGciOiJIUzI1NiIs...` | 中 |
| `SUPABASE_SERVICE_ROLE_KEY` | 服务角色 Key | `eyJhbGciOiJIUzI1NiIs...` | 🔴 高 |

**获取方式：**
1. 进入 Supabase Dashboard
2. Project Settings → API
3. Project URL → `SUPABASE_URL`
4. anon public → `SUPABASE_ANON_KEY`
5. service_role secret → `SUPABASE_SERVICE_ROLE_KEY`

### 2.2 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SUPABASE_DB_URL` | 数据库连接串 | 自动从 SUPABASE_URL 派生 |
| `SITE_URL` | 网站 URL | `http://localhost:3000` |
| `ADDITIONAL_REDIRECT_URLS` | 额外重定向 URL | - |
| `JWT_EXPIRY` | JWT 过期时间 | 3600 (1小时) |

---

## 三、前端环境变量

### 3.1 必需变量 (.env.local)

```bash
# Supabase 配置
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...

# 注意: NEXT_PUBLIC_ 前缀的变量会暴露在客户端
```

### 3.2 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NEXT_PUBLIC_APP_NAME` | 应用名称 | CET 英语四级学习系统 |
| `NEXT_PUBLIC_APP_URL` | 应用 URL | http://localhost:3000 |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | 启用分析 | false |
| `NEXT_PUBLIC_THEME` | 主题 | theme-sass |

### 3.3 第三方服务 (可选)

```bash
# Google Analytics
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Sentry
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## 四、后端环境变量 (Edge Functions)

### 4.1 必需变量

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...

# JWT 配置
JWT_SECRET=your-32-character-secret-key-here
```

### 4.2 AI 服务配置

```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_API_BASE_URL=https://api.deepseek.com
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60

# 备用 API Keys (可选，多个用逗号分隔)
DEEPSEEK_BACKUP_KEYS=sk-xxx1,sk-xxx2
```

### 4.3 存储配置

```bash
# 文件存储 (使用 Supabase Storage)
STORAGE_BUCKET_AVATARS=avatars
STORAGE_BUCKET_COURSES=course-covers
STORAGE_BUCKET_AUDIO=audio
STORAGE_BUCKET_DOCUMENTS=documents
```

---

## 五、生产环境变量

### 5.1 生产环境 .env.production

```bash
# ====================
# Supabase 生产配置
# ====================
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...

# ====================
# JWT 密钥 (必须修改)
# ====================
JWT_SECRET=生成一个32位以上的随机字符串
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# ====================
# 数据库 (Supabase 管理)
# ====================
POSTGRES_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# ====================
# AI 服务
# ====================
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_API_BASE_URL=https://api.deepseek.com

# ====================
# 应用配置
# ====================
APP_ENV=production
APP_URL=https://your-domain.com
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# ====================
# 监控 (可选)
# ====================
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 5.2 生成 JWT_SECRET 的方法

```bash
# 方法 1: OpenSSL
openssl rand -base64 32

# 方法 2: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

---

## 六、CI/CD 环境变量

### 6.1 GitHub Secrets

| Secret 名称 | 说明 | 必填 |
|-------------|------|------|
| `SUPABASE_PROJECT_REF` | 项目引用 ID | ✅ |
| `SUPABASE_DB_PASSWORD` | 数据库密码 | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | 服务角色 Key | ✅ |
| `VERCEL_TOKEN` | Vercel Token | ✅ |
| `VERCEL_ORG_ID` | Vercel 组织 ID | ✅ |
| `VERCEL_PROJECT_ID` | Vercel 项目 ID | ✅ |

### 6.2 GitHub Actions 变量

| 变量名称 | 说明 | 值来源 |
|----------|------|--------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL | Supabase Dashboard |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | 匿名 Key | Supabase Dashboard |

---

## 七、本地开发环境变量

### 7.1 .env.local 模板

```bash
# ====================
# 开发环境配置
# ====================

# Supabase (本地开发)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...

# 注意: 本地开发使用 supabase CLI 的服务角色 Key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...

# ====================
# 本地 AI 服务 (开发)
# ====================
# 开发环境可以使用 mock 或本地模型
DEEPSEEK_API_KEY=sk-dev-mock-key
DEEPSEEK_API_BASE_URL=http://localhost:8000

# ====================
# 开发配置
# ====================
APP_ENV=development
DEBUG=true
LOG_LEVEL=debug
```

### 7.2 Supabase 本地开发

```bash
# 启动本地 Supabase
npx supabase start

# 本地 URL
# API: http://localhost:54321
# DB: postgresql://postgres:postgres@localhost:54322/postgres
# Studio: http://localhost:54323
```

---

## 八、环境检查脚本

### 8.1 验证环境变量

```typescript
// lib/env.ts
const requiredEnvVars = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  'SUPABASE_SERVICE_ROLE_KEY',
] as const

export function validateEnv() {
  const missing = requiredEnvVars.filter(
    (key) => !process.env[key]
  )
  
  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(', ')}`
    )
  }
}

// 在应用启动时调用
validateEnv()
```

---

## 九、迁移检查清单

| 变量 | 开发 | 测试 | 生产 | 状态 |
|------|------|------|------|------|
| SUPABASE_URL | ✅ | ✅ | ✅ | ⬜ |
| SUPABASE_ANON_KEY | ✅ | ✅ | ✅ | ⬜ |
| SUPABASE_SERVICE_ROLE_KEY | ✅ | ✅ | ✅ | ⬜ |
| JWT_SECRET | - | - | ✅ | ⬜ |
| DEEPSEEK_API_KEY | ⚠️ | ⚠️ | ✅ | ⬜ |
| NEXT_PUBLIC_APP_URL | - | - | ✅ | ⬜ |

---

## 十、安全最佳实践

### 10.1 敏感信息

| 信息 | 存储位置 | 说明 |
|------|---------|------|
| `SUPABASE_SERVICE_ROLE_KEY` | 服务端 | 不能暴露给客户端 |
| `JWT_SECRET` | 服务端 | 不能暴露给客户端 |
| `DEEPSEEK_API_KEY` | 服务端 | Edge Functions 中使用 |

### 10.2 客户端安全

```typescript
// ✅ 正确: 使用 NEXT_PUBLIC_ 前缀
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co

// ❌ 错误: 将敏感信息添加到客户端
NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### 10.3 环境变量管理流程

```
1. 本地开发 → .env.local
2. Git 不追踪 .env.local
3. 测试环境 → GitHub Secrets
4. 生产环境 → Vercel Environment Variables
```

---

**文档结束**
