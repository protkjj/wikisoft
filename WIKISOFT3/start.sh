#!/bin/bash
# WIKISOFT3 백엔드 + 프론트엔드 + 브라우저 동시 실행

cd "$(dirname "$0")"

echo "🚀 WIKISOFT3 시작..."

# 기존 프로세스 정리
lsof -ti:8004 | xargs kill -9 2>/dev/null
lsof -ti:3005 | xargs kill -9 2>/dev/null
sleep 1

# 백엔드 실행 (nohup으로 안정적 실행)
source ../.venv/bin/activate
nohup bash -c "cd $(pwd) && PYTHONPATH=$(pwd) uvicorn external.api.main:app --reload --port 8004" > /tmp/wikisoft3_backend.log 2>&1 &
BACKEND_PID=$!

sleep 2

# 프론트엔드 실행 (nohup으로 안정적 실행)
cd frontend
nohup npm run dev > /tmp/wikisoft3_frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "✅ 백엔드:    http://localhost:8004 (PID: $BACKEND_PID)"
echo "✅ 프론트엔드: http://localhost:3005 (PID: $FRONTEND_PID)"
echo ""

# 3초 대기 후 브라우저 열기
sleep 3
open http://localhost:3005

echo "🌐 브라우저 열림!"
echo ""
echo "로그 확인:"
echo "  백엔드:    tail -f /tmp/wikisoft3_backend.log"
echo "  프론트엔드: tail -f /tmp/wikisoft3_frontend.log"
echo ""
echo "종료하려면: kill $BACKEND_PID $FRONTEND_PID"


