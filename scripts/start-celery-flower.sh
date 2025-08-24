#!/bin/bash

# Celery Flower (监控界面) 启动脚本

echo "🌸 启动Celery Flower监控界面..."

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动Flower监控界面
celery -A app.core.celery_app flower \
    --port=5555 \
    --broker=redis://localhost:6379/0 \
    --basic_auth=admin:admin123 \
    --url_prefix=flower
