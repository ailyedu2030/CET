#!/bin/bash

# Celery Beat (定时任务调度器) 启动脚本

echo "⏰ 启动Celery Beat定时任务调度器..."

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 创建logs目录
mkdir -p logs

# 启动Celery Beat
celery -A app.core.celery_app beat \
    --loglevel=info \
    --pidfile=/tmp/celery_beat.pid \
    --logfile=logs/celery_beat.log \
    --schedule=logs/celerybeat-schedule
