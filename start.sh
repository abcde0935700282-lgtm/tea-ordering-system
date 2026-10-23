#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================="
echo "  🚀 智能線上點餐系統 啟動中..."
echo "=========================================="

if [ ! -d ".venv" ]; then
    echo "建立 Python 虛擬環境..."
    /Users/urista/.local/bin/uv venv --python 3.11
    /Users/urista/.local/bin/uv pip install fastapi uvicorn python-multipart pyjwt passlib bcrypt aiofiles
fi

echo "正在啟動伺服器 (http://127.0.0.1:8000)..."
exec .venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --reload
