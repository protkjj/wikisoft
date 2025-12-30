from openai import OpenAI
from typing import Dict, List
import json
import os
import pandas as pd


class AIProcessor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
    
    def normalize_data(self, df_sample: List[Dict], diagnostic_answers: Dict[str, str]) -> Dict:
        """
        데이터 정규화
        
        Args:
            df_sample: DataFrame의 샘플 (dict 형태)
            diagnostic_answers: {"q1": "현직만", ...}
        
        Returns:
            {
                "normalized_rows": [
                    {"row": 0, "columns": {"전화": "01012345678", ...}, "confidence": 0.95}
                ]
            }
        """
        try:
            from .prompts import create_normalize_prompt
            
            prompt = create_normalize_prompt(df_sample, diagnostic_answers)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 한국 HR 데이터 정규화 전문가입니다. JSON 형식으로만 응답하세요."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # 응답 파싱
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return result
        
        except json.JSONDecodeError:
            # JSON 파싱 실패 → 안전 폴백
            return {"normalized_rows": [], "confidence": 0}
        except Exception as e:
            print(f"정규화 오류: {e}")
            return {"normalized_rows": [], "confidence": 0}
    
    def build_questions(self, errors: List[Dict], anomalies: List[Dict]) -> Dict:
        """
        챗봇 질문 생성
        
        Args:
            errors: Layer 1 검증 에러 목록
            anomalies: Layer 2 이상치 목록
        
        Returns:
            {
                "questions": [...],
                "batch_groups": [...]
            }
        """
        try:
            from .prompts import create_questions_prompt
            
            prompt = create_questions_prompt(errors, anomalies)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 HR 데이터 검증 전문가입니다. 사용자를 위한 질문만 생성하세요. JSON 형식으로만 응답하세요."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # 응답 파싱
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return result
        
        except json.JSONDecodeError:
            return {"questions": [], "batch_groups": []}
        except Exception as e:
            print(f"질문 생성 오류: {e}")
            return {"questions": [], "batch_groups": []}
            
            # 4. 급여 범위 체크 (0 < 급여 < 100,000,000)
            try:
                salary = float(str(row.get('기준급여', '')).replace(',', ''))
                if salary <= 0 or salary >= 100000000:
                    row_errors.append({
                        "column": "기준급여",
                        "error": f"범위 오류: {int(salary)} (0 < 급여 < 100,000,000)"
                    })
            except (ValueError, TypeError):
                pass
            
            # 5. 퇴직금 범위 체크 (0 이상)
            try:
                retire_fund = float(str(row.get('당년도퇴직금추계액', '')).replace(',', ''))
                if retire_fund < 0:
                    row_errors.append({
                        "column": "당년도퇴직금추계액",
                        "error": "음수 오류: 퇴직금은 0 이상이어야 함"
                    })
            except (ValueError, TypeError):
                pass
            
            # 오류가 있으면 기록
            if row_errors:
                errors.append({
                    "row": idx,
                    "errors": row_errors
                })
        
        return {"validation_errors": errors}
    
    def _call_ai_model(self, prompt: str) -> list:
        """OpenAI API로 데이터 정규화 요청"""
        try:
            client = OpenAI(api_key=self.__api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 HR 데이터 정규화 전문가입니다. 반드시 JSON 형식으로만 응답하세요."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # 일관성 중요
                max_tokens=4096
            )
            
            # 응답에서 JSON 추출
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            
            return result.get("normalized", [])
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return []
        except Exception as e:
            print(f"OpenAI API 호출 오류: {e}")
            return []
    
    def chat(self, df: pd.DataFrame, query: str) -> dict:
        return {"response": "AI disabled", "function_call": None}
    
