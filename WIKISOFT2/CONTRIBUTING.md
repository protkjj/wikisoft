# 🤝 기여 가이드 (CONTRIBUTING)

**버전**: 2.1  
**최종 업데이트**: 2025-12-26

---

## 📦 개발 환경

- Python 3.12+ (venv 권장)
- FastAPI, Uvicorn, pandas, openpyxl, xlrd
- 선택: OpenAI (GPT-4o), python-dotenv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🧑‍💻 코딩 규칙

- 타입 힌트 사용: 함수 입출력에 타입 명시
- 가독성: 의미 있는 변수명, 한 줄 120자 이하 권장
- 예외 처리: 사용자 입력/파일 파싱/AI 응답에 대한 안전 처리
- 로깅: 구조화 로깅 사용, 에러는 실제 치명적일 때만
- 테스트 우선: 기능 추가 시 가까운 단위 테스트/통합 테스트 동반

---

## 🌿 브랜치 전략

- `main`: 안정 릴리스
- `develop`: 다음 릴리스 준비
- `feat/<name>`: 기능 추가 브랜치
- `fix/<name>`: 버그 수정 브랜치

PR 체크리스트:
- [ ] 테스트 추가/갱신
- [ ] 문서(README/ARCHITECTURE/CHANGELOG) 갱신
- [ ] 타입/예외/로깅 점검
- [ ] PII/보안 준수 확인

---

## 🧪 테스트 실행

```bash
python tests/test_layer2_integration.py
python tests/test_ai_header_matching.py
python tests/test_api_warnings.py
```

---

## 🔒 개인정보/AI 사용 지침

- 기본 폴백 모드: 외부 전송 없음, 로컬 처리
- AI 모드: 헤더 중심 비교(PII 미전송), `utils/masking.py`로 민감정보 제거
- 로그에 PII 저장 금지, 샘플 데이터도 마스킹된 형태로 공유

---

## 📝 커밋 메시지 포맷

```
feat(column-matcher): add alias support and normalization
fix(layer2): handle zero division in diff_percent
docs(readme): add operating modes and privacy section
```

---

## 📣 커뮤니케이션

- 이슈에는 재현 단계/기대 결과/실제 결과를 구체적으로 기술
- 논의된 결정은 CHANGELOG와 SPEC에 반영해 온보딩 비용 최소화
