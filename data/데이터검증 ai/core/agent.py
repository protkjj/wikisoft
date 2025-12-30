"""
AI 에이전트 정의
계리 지식을 바탕으로 데이터를 검증하는 AI 에이전트
"""

from typing import Dict, List, Any
import pandas as pd
from langchain_openai import ChatOpenAI


class AuditAgent:
    """확정급여채무평가 데이터를 검증하는 AI 에이전트"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키
            model_name: 사용할 모델 이름 (기본값: gpt-4o-mini)
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            openai_api_key=api_key
        )
        self.api_key = api_key
    
    def _get_audit_prompt(self) -> str:
        """
        계리 감사를 위한 프롬프트 생성
        
        Returns:
            검증 지침이 담긴 프롬프트 문자열
        """
        prompt = """당신은 퇴직연금 계리사입니다.

엑셀 데이터를 읽어보고, 다음 규칙에 따라 이상한 부분이 있는지 확인하세요:

1. **사원번호 중복 확인** (매우 중요):
   - 재직자 명부 내부에서 사원번호 중복 확인 (같은 명부에 같은 사원번호가 2번 이상 나타나는지)
   - 퇴직자 명부 내부에서 사원번호 중복 확인
   - 재직자 명부와 퇴직자 명부 간 사원번호 중복 확인 (같은 사원번호가 두 명부에 동시에 존재하는지)
2. 중간정산자가 재직자 명부에 있는지 확인
3. 날짜 순서 확인 (생년월일 < 입사일 < 중간정산일 < 퇴직일 < 2022.12.31)
4. 근속기간 1년 이상인데 퇴직금이 0원인 경우 확인

**중요: 이상한 부분을 발견하면 반드시 구체적인 정보를 포함하세요:**
- 사원번호 (예: 사원번호 190001)
- 이름 (예: 김철수님)
- 날짜 (예: 2022년 3월 15일)
- 구체적인 문제점 (예: 재직자 명부와 퇴직자 명부에 동시에 존재)

예시:
"담당자님, 재직자 명부에서 사원번호 190001 김철수님이 2번 나타나고 있습니다. 같은 명부 내에서 중복되어 있어 평가액이 중복 산출될 위험이 있습니다. 확인 부탁드립니다."

"담당자님, 사원번호 190001 김철수님의 데이터에 중복이 발생하고 있습니다. 재직자 명부와 퇴직자 명부에 동시에 존재하는데, 이는 평가액이 중복 산출될 위험이 있습니다. 확인 부탁드립니다."

"담당자님, 김철수님(사원번호: 190001)의 경우 2022년에 중간정산을 하셨는데 퇴직자 명부에 들어있습니다. 중간정산자는 재직자이므로 재직자 명부로 옮겨주셔야 정확한 계리 평가가 가능합니다."

"담당자님, 이영희님(사원번호: 190002)은 2022년에 퇴직하셨는데 2021년 명부에 없습니다. 확인 부탁드립니다."

문제가 없으면 "담당자님, 이 시트의 데이터를 검토한 결과 특별한 문제가 발견되지 않았습니다."라고 작성하세요.
"""
        return prompt
    
    def audit_data(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        여러 DataFrame을 검증하고 결과를 반환
        
        Args:
            dataframes: {시트명: DataFrame} 형태의 딕셔너리
            
        Returns:
            검증 결과 딕셔너리
        """
        audit_results = {
            "sheets_audited": [],
            "findings": [],
            "summary": ""
        }
        
        # 각 시트별로 검증 수행
        for sheet_name, df in dataframes.items():
            print(f"      - {sheet_name} 검증 중...")
            
            try:
                # DataFrame을 텍스트로 변환 (AI가 읽을 수 있게)
                # 데이터가 너무 크면 처음 1000행만 사용
                if len(df) > 1000:
                    data_text = f"총 {len(df)}행 중 상위 1000행:\n{df.head(1000).to_string()}"
                else:
                    data_text = df.to_string()
                
                # 프롬프트 작성
                prompt = self._get_audit_prompt()
                prompt += f"\n\n시트명: '{sheet_name}'\n"
                prompt += f"컬럼명: {list(df.columns)}\n"
                prompt += f"데이터:\n{data_text}\n"
                prompt += "\n위 데이터를 읽어보고 이상한 부분이 있으면 피드백을 작성하세요."
                
                # AI에게 직접 질문 (코드 실행 없이)
                response = self.llm.invoke(prompt)
                result_text = response.content
                
                audit_results["sheets_audited"].append(sheet_name)
                audit_results["findings"].append({
                    "sheet": sheet_name,
                    "result": result_text
                })
                
            except Exception as e:
                error_msg = f"시트 '{sheet_name}' 검증 중 오류 발생: {str(e)}"
                audit_results["findings"].append({
                    "sheet": sheet_name,
                    "result": error_msg,
                    "error": True
                })
        
        # 전체 요약 생성
        audit_results["summary"] = self._generate_summary(audit_results)
        
        return audit_results
    
    def _generate_summary(self, audit_results: Dict[str, Any]) -> str:
        """
        검증 결과 요약 생성
        
        Args:
            audit_results: 검증 결과 딕셔너리
            
        Returns:
            요약 텍스트
        """
        total_sheets = len(audit_results["sheets_audited"])
        findings_count = len([f for f in audit_results["findings"] if not f.get("error", False)])
        
        summary = f"총 {total_sheets}개 시트를 검증했습니다. "
        summary += f"{findings_count}개 시트에서 검증 결과를 확인했습니다."
        
        return summary
