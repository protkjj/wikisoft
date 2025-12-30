#!/bin/bash

echo "=== AI Agent 테스트 ==="
echo ""

echo "1️⃣ 시스템 설명 요청 (RAG 지식 활용)"
curl -s -X POST http://localhost:8003/api/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "이 시스템이 뭐하는 거야?"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('답변:', d.get('answer', '')[:200], '...')
print('제공자:', d.get('provider'))
print('툴 사용:', d.get('used_tools', []))
"

echo ""
echo "2️⃣ 진단 질문 목록 요청 (툴 호출)"
curl -s -X POST http://localhost:8003/api/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "검증에 사용하는 질문 목록 보여줘"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('답변:', d.get('answer', '')[:200], '...')
print('제공자:', d.get('provider'))
print('툴 사용:', d.get('used_tools', []))
"

echo ""
echo "3️⃣ 시스템 도구 목록 요청 (툴 호출)"
curl -s -X POST http://localhost:8003/api/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "사용 가능한 검증 도구 알려줘"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('답변:', d.get('answer', '')[:200], '...')
print('제공자:', d.get('provider'))
print('툴 사용:', d.get('used_tools', []))
"

echo ""
echo "✅ 테스트 완료!"
