# Excel AI 검증 수식 가이드

## 옵션 1: Claude for Google Sheets

Google Sheets에서 Claude AI를 직접 사용할 수 있습니다.

### 설치
1. Google Sheets 열기
2. 확장 프로그램 → 부가기능 → 부가기능 설치
3. "Claude for Sheets" 검색 후 설치
4. API 키 설정

### 검증 수식 예시

```
=CLAUDE("다음 명부 데이터를 검증해줘. 오류가 있으면 알려줘:
- 입사일이 생년월일보다 빠르면 오류
- 급여가 음수면 오류
- 필수값(사원번호, 성명, 입사일) 누락 체크

데이터:", A1:H100)
```

### 인원수 검증

```
=CLAUDE("재직자 수를 확인해줘.
임원(직종구분=3): 몇 명?
직원(직종구분=1,2): 몇 명?
계약직(직종구분=4): 몇 명?

데이터:", A1:H100)
```

---

## 옵션 2: Microsoft Copilot (Excel)

Microsoft 365 구독자는 Excel에서 Copilot 사용 가능

### 사용법
1. Excel에서 데이터 선택
2. Copilot 패널 열기
3. "이 데이터에서 이상치를 찾아줘" 입력

### 프롬프트 예시

```
이 재직자 명부를 검증해줘:
1. 입사일 > 생년월일 확인
2. 급여 음수 값 찾기
3. 필수 필드 누락 찾기
4. 중복 사원번호 찾기
```

---

## 옵션 3: VBA + API (고급)

직접 API를 호출하여 검증 실행

### VBA 코드

```vba
Sub ValidateRoster()
    ' Claude API 호출하여 검증
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")

    ' 데이터 수집
    Dim data As String
    data = GetRosterData() ' 명부 데이터를 JSON으로 변환

    ' API 호출
    http.Open "POST", "https://api.anthropic.com/v1/messages", False
    http.setRequestHeader "x-api-key", "YOUR_API_KEY"
    http.setRequestHeader "Content-Type", "application/json"
    http.send(data)

    ' 결과 처리
    MsgBox http.responseText
End Sub
```

---

## 옵션 4: Python 스크립트 연동

Excel → Python → Telegram 알림

```python
# validate_and_notify.py
import pandas as pd
from telegram.notifications import notify_validation

# Excel 읽기
df = pd.read_excel("명부.xlsx")

# 검증 로직
errors = validate(df)

# Telegram 알림
await notify_validation(
    filename="명부.xlsx",
    status="ok" if not errors else "error",
    errors=len(errors),
    warnings=0,
    row_count=len(df),
)
```

---

## 권장 방식

| 상황 | 권장 옵션 |
|-----|----------|
| Google Sheets 사용 | Claude for Sheets |
| Microsoft 365 구독 | Copilot |
| 자동화 필요 | Python 스크립트 |
| 오프라인 환경 | VBA + 로컬 검증 |
