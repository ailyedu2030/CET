# 英语四级学习系统 - 主应用容器
# 基于Python 3.11官方镜像，支持FastAPI应用和前端静态文件服务
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY requirements.txt .
COPY pyproject.toml .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 复制前端源码并构建
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# 回到应用根目录
WORKDIR /app

# 复制应用源码
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# 创建必要的目录
RUN mkdir -p /app/logs
RUN mkdir -p /app/uploads
RUN mkdir -p /app/reports
RUN mkdir -p /app/static

# 复制前端构建产物到静态文件目录
RUN cp -r /app/frontend/dist/* /app/static/

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]