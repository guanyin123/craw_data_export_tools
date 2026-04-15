#!/bin/bash
# 后端启动脚本

cd "$(dirname "$0")"
export PYTHONPATH=backend:$PYTHONPATH
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
