"""
Prompt Configuration Manager

LLM 프롬프트 설정 중앙 관리
현재: 하드코딩된 프롬프트
미래: YAML/DB에서 로드 가능
"""

from typing import Dict, Optional
import os
import json

try:
    import yaml  # 선택적 의존성: 없으면 JSON만 지원
except Exception:
    yaml = None


class PromptConfig:
    """프롬프트 설정 관리"""
    
    # 현재: 하드코딩된 프롬프트들
    _PROMPTS = {
        "column_matching": {
            "system": """당신은 Excel 헤더 매칭 전문가입니다.

주어진 표준 스키마와 사용자의 Excel 헤더를 분석하여 올바른 매칭을 제시합니다.

표준 스키마:
- employee_type: 직원 유형 (정규직, 비정규직, 임시직 등)
- name: 직원 이름
- salary: 월급
- department: 부서명
- position: 직급
- join_date: 입사일
- status: 근무 상태 (재직, 휴직, 퇴직 등)

규칙:
1. 정확도가 95% 이상이면 자동 매칭
2. 60-95% 사이면 "사람 확인" 제시
3. 60% 미만이면 "매칭 불가" 표시
4. 다중 매칭 가능 (예: "급여" = salary)

응답 형식:
{
    "matches": [
        {"source": "Excel헤더", "target": "표준필드", "confidence": 0.95},
        ...
    ],
    "unmatched": ["매칭 불가능한 헤더"],
    "notes": "추가 설명"
}""",
            "user_template": "다음 Excel 헤더를 표준 스키마로 매칭하세요:\n{headers}"
        },
        
        "data_validation": {
            "system": """당신은 데이터 검증 전문가입니다.

주어진 데이터가 비즈니스 규칙을 따르는지 확인합니다.

검증 규칙:
1. 필수 필드: name, employee_type, salary, status
2. 급여 범위: 0 < salary < 1,000,000,000
3. 날짜 형식: YYYY-MM-DD
4. 상태 값: 재직, 휴직, 퇴직, 해고
5. 이상치: 급여 변동이 전월 대비 50% 이상 → 플래그

응답:
{
    "valid": true/false,
    "errors": [...],
    "warnings": [...],
    "confidence": 0.0-1.0
}""",
            "user_template": "다음 데이터를 검증하세요:\n{data}"
        },
        
        "anomaly_detection": {
            "system": """당신은 이상치 탐지 전문가입니다.

데이터에서 비정상적인 패턴을 찾습니다.

이상치 정의:
1. 급여 이상: 통상 급여의 2배 이상 또는 1/10 이하
2. 날짜 이상: 미래 날짜, 불가능한 범위
3. 논리 이상: 퇴직자의 급여, 미입사자의 근무기록
4. 통계적 이상: Z-score > 3""",
            "user_template": "다음 데이터에서 이상치를 찾으세요:\n{data}"
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        초기화
        
        Args:
            config_file: 설정 파일 경로 (현재는 무시, 미래용)
        """
        self.config_file = config_file
        self._prompts = self._PROMPTS.copy()
    
    def get_system_prompt(self, prompt_name: str) -> Optional[str]:
        """
        시스템 프롬프트 조회
        
        Args:
            prompt_name: 프롬프트 이름
        
        Returns:
            프롬프트 텍스트 또는 None
        """
        prompt = self._prompts.get(prompt_name, {})
        return prompt.get("system")
    
    def get_user_template(self, prompt_name: str) -> Optional[str]:
        """
        사용자 템플릿 조회
        
        Args:
            prompt_name: 프롬프트 이름
        
        Returns:
            템플릿 텍스트 또는 None
        """
        prompt = self._prompts.get(prompt_name, {})
        return prompt.get("user_template")
    
    def get_full_prompt(self, prompt_name: str, **kwargs) -> Dict[str, str]:
        """
        전체 프롬프트 조회 (포맷팅 포함)
        
        Args:
            prompt_name: 프롬프트 이름
            **kwargs: 템플릿 변수들
        
        Returns:
            {"system": ..., "user": ...}
        """
        prompt = self._prompts.get(prompt_name, {})
        system = prompt.get("system", "")
        user_template = prompt.get("user_template", "")
        
        try:
            user = user_template.format(**kwargs)
        except KeyError:
            user = user_template
        
        return {
            "system": system,
            "user": user
        }
    
    def update_prompt(self, prompt_name: str, system: str = None, user_template: str = None) -> bool:
        """
        프롬프트 업데이트
        
        Args:
            prompt_name: 프롬프트 이름
            system: 새로운 시스템 프롬프트
            user_template: 새로운 사용자 템플릿
        
        Returns:
            True if successful
        """
        if prompt_name not in self._prompts:
            return False
        
        if system:
            self._prompts[prompt_name]["system"] = system
        if user_template:
            self._prompts[prompt_name]["user_template"] = user_template
        
        return True
    
    def add_prompt(self, prompt_name: str, system: str, user_template: str) -> bool:
        """
        새로운 프롬프트 추가
        
        Args:
            prompt_name: 프롬프트 이름
            system: 시스템 프롬프트
            user_template: 사용자 템플릿
        
        Returns:
            True if successful
        """
        if prompt_name in self._prompts:
            return False
        
        self._prompts[prompt_name] = {
            "system": system,
            "user_template": user_template
        }
        return True
    
    def load_from_file(self, file_path: str) -> bool:
        """
        YAML/JSON에서 프롬프트 로드 (외부 설정 병합)
        
        Args:
            file_path: 설정 파일 경로
        
        Returns:
            True if successful
        """
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.lower().endswith(('.yml', '.yaml')) and yaml is not None:
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)

            # 외부 파일은 {"prompts": {name: {system:.., user_template:..}}} 권장
            external_prompts = data.get("prompts") if isinstance(data, dict) else None
            if isinstance(external_prompts, dict):
                # 하드코딩 프롬프트에 병합 (외부 설정 우선 적용)
                for name, cfg in external_prompts.items():
                    if isinstance(cfg, dict):
                        system = cfg.get("system")
                        user_template = cfg.get("user_template")
                        if name in self._prompts:
                            if system:
                                self._prompts[name]["system"] = system
                            if user_template:
                                self._prompts[name]["user_template"] = user_template
                        else:
                            self._prompts[name] = {
                                "system": system or "",
                                "user_template": user_template or ""
                            }
                return True
            return False
        except Exception:
            return False
    
    def list_prompts(self) -> list:
        """
        사용 가능한 프롬프트 목록
        
        Returns:
            프롬프트 이름 목록
        """
        return list(self._prompts.keys())


# 전역 인스턴스
_global_prompt_config = PromptConfig()


def get_prompt_config() -> PromptConfig:
    """전역 PromptConfig 조회"""
    return _global_prompt_config
