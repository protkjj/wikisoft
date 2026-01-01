#!/bin/bash
# WIKISOFT3 + Windmill 로컬 전체 실행

echo "🚀 WIKISOFT3 + Windmill 시작..."

# 1. Windmill 실행 (Docker)
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker가 실행 중이 아닙니다. Docker Desktop을 시작해주세요."
    exit 1
fi

echo "📦 Windmill 컨테이너 시작..."
docker run -d --name windmill \
    -p 8000:8000 \
    -e DATABASE_URL=postgres://postgres:changeme@host.docker.internal:5432/windmill \
    ghcr.io/windmill-labs/windmill:main 2>/dev/null || \
    docker start windmill

# 2. WIKISOFT3 백엔드 실행
echo "🔧 WIKISOFT3 백엔드 시작..."
cd /Users/kj/Desktop/wiki/WIKISOFT3
source ../.venv/bin/activate
PYTHONPATH=$(pwd) uvicorn external.api.main:app --reload --port 8003 &
BACKEND_PID=$!

# 3. 프론트엔드 실행
echo "🎨 프론트엔드 시작..."
cd frontend
npm run dev -- --port 3004 &
FRONTEND_PID=$!

sleep 3

echo ""
echo "✅ Windmill:     http://localhost:8000"
echo "✅ 백엔드 API:   http://localhost:8003"
echo "✅ 프론트엔드:   http://localhost:3004"
echo ""
echo "💡 Windmill에서 API 호출 시:"
echo "   api_url = 'http://host.docker.internal:8003'"
echo ""
echo "종료하려면 Ctrl+C"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker stop windmill; exit" SIGINT SIGTERM

wait
