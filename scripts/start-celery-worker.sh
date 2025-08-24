#!/bin/bash

# Celery Worker 启动脚本

echo "🚀 启动Celery Worker..."

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动Celery Worker
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=general_queue,ai_queue,training_queue \
    --hostname=worker1@%h \
    --time-limit=1800 \
    --soft-time-limit=1200 \
    --max-tasks-per-child=1000 \
    --pidfile=/tmp/celery_worker.pid \
    --logfile=logs/celery_worker.log
