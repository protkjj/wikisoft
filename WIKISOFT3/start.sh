#!/bin/bash
# WIKISOFT3 백엔드 + 프론트엔드 동시 실행

echo "🚀 WIKISOFT3 시작..."

# 백엔드 실행 (백그라운드)
cd /Users/kj/Desktop/wiki/WIKISOFT3
source ../.venv/bin/activate
PYTHONPATH=$(pwd) uvicorn external.api.main:app --reload --port 8003 &
BACKEND_PID=$!

# 프론트엔드 실행 (백그라운드)
cd frontend
npm run dev -- --port 3004 &
FRONTEND_PID=$!

echo ""
echo "✅ 백엔드:    http://localhost:8003"
echo "✅ 프론트엔드: http://localhost:3004"
echo ""
echo "종료하려면 Ctrl+C"

# Ctrl+C 시 둘 다 종료
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# 대기
wait
