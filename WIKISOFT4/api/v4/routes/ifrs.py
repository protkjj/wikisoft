"""
IFRS 1019 퇴직급여 계산 API

Step 2: 명부 검증 후 퇴직급여채무(DBO) 계산

엔드포인트:
- POST /calculate: 퇴직급여채무 계산
- POST /calculate-from-file: 파일에서 직접 계산
- GET /assumptions/default: 기본 보험수리적 가정 조회
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.calculators.ifrs1019 import (
    IFRS1019Calculator,
    ActuarialAssumptions,
    EmployeeData,
    EmployeeType,
    PlanType,
    parse_employee_from_dict,
)
from core.agent.tool_registry import get_registry
from core.utils.security import validate_upload_file

router = APIRouter(prefix="/ifrs", tags=["IFRS 1019"])


# ============================================================
# Request/Response Models
# ============================================================

class AssumptionsInput(BaseModel):
    """보험수리적 가정 입력"""
    discount_rate: float = Field(0.045, ge=0, le=0.2, description="할인율 (예: 0.045 = 4.5%)")
    salary_growth_rate: float = Field(0.03, ge=0, le=0.2, description="임금상승률")
    inflation_rate: float = Field(0.02, ge=0, le=0.1, description="물가상승률")
    retirement_age: int = Field(60, ge=50, le=70, description="정년")
    mortality_rate: float = Field(0.001, ge=0, le=0.1, description="사망률")
    turnover_rate: float = Field(0.05, ge=0, le=0.5, description="퇴직률")
    severance_multiplier: float = Field(1.0, ge=0.5, le=3.0, description="퇴직금 지급률")
    valuation_date: Optional[str] = Field(None, description="평가기준일 (YYYY-MM-DD)")


class EmployeeInput(BaseModel):
    """직원 데이터 입력"""
    employee_id: str = Field(..., description="사원번호")
    name: str = Field(..., description="이름")
    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    hire_date: str = Field(..., description="입사일 (YYYY-MM-DD)")
    base_salary: int = Field(..., gt=0, description="기준급여 (월)")
    employee_type: Optional[str] = Field("정규직", description="종업원구분 (임원/정규직/계약직)")
    plan_type: Optional[str] = Field("DB", description="제도구분 (DB/DC)")


class CalculateRequest(BaseModel):
    """퇴직급여 계산 요청"""
    employees: List[EmployeeInput] = Field(..., min_length=1, description="직원 목록")
    assumptions: Optional[AssumptionsInput] = Field(None, description="보험수리적 가정")


class EmployeeResultResponse(BaseModel):
    """직원별 결과"""
    employee_id: str
    name: str
    age: int
    service_years: float
    years_to_retirement: float
    current_salary: int
    projected_salary: int
    dbo: int
    service_cost: int
    interest_cost: int
    projected_benefit: int
    vested_benefit: int


class SummaryResponse(BaseModel):
    """요약 결과"""
    total_employees: int
    total_dbo: int
    total_service_cost: int
    total_interest_cost: int
    total_projected_benefit: int
    average_age: float
    average_service_years: float
    average_dbo: int


class CalculateResponse(BaseModel):
    """퇴직급여 계산 응답"""
    success: bool
    summary: SummaryResponse
    assumptions: Dict[str, Any]
    employees: List[EmployeeResultResponse]
    metadata: Dict[str, Any]


# ============================================================
# API Endpoints
# ============================================================

@router.post("/calculate", response_model=CalculateResponse)
async def calculate_dbo(request: CalculateRequest):
    """
    퇴직급여채무(DBO) 계산

    IFRS 1019 (K-IFRS 제1019호)에 따른 확정급여채무 계산.
    예측단위적립방식(Projected Unit Credit Method) 적용.

    Input:
    - employees: 직원 목록 (사원번호, 이름, 생년월일, 입사일, 기준급여)
    - assumptions: 보험수리적 가정 (선택, 기본값 사용 가능)

    Output:
    - summary: 전체 요약 (총 DBO, 근무원가, 이자원가)
    - employees: 직원별 상세 결과
    """
    try:
        # 보험수리적 가정 설정
        if request.assumptions:
            assumptions = ActuarialAssumptions(
                discount_rate=request.assumptions.discount_rate,
                salary_growth_rate=request.assumptions.salary_growth_rate,
                inflation_rate=request.assumptions.inflation_rate,
                retirement_age=request.assumptions.retirement_age,
                mortality_rate=request.assumptions.mortality_rate,
                turnover_rate=request.assumptions.turnover_rate,
                severance_multiplier=request.assumptions.severance_multiplier,
                valuation_date=date.fromisoformat(request.assumptions.valuation_date)
                    if request.assumptions.valuation_date else date.today(),
            )
        else:
            assumptions = ActuarialAssumptions()

        # 직원 데이터 변환
        employees = []
        for emp_input in request.employees:
            emp = parse_employee_from_dict(emp_input.model_dump())
            employees.append(emp)

        # 계산 실행
        calculator = IFRS1019Calculator(assumptions)
        result = calculator.calculate(employees)

        # 응답 생성
        result_dict = result.to_dict()

        return CalculateResponse(
            success=True,
            summary=SummaryResponse(**result_dict["summary"]),
            assumptions=result_dict["assumptions"],
            employees=[EmployeeResultResponse(**e) for e in result_dict["employees"]],
            metadata=result_dict["metadata"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계산 중 오류 발생: {str(e)}")


@router.post("/calculate-from-file")
async def calculate_from_file(
    file: UploadFile = File(...),
    discount_rate: float = Form(0.045),
    salary_growth_rate: float = Form(0.03),
    retirement_age: int = Form(60),
    turnover_rate: float = Form(0.05),
):
    """
    파일에서 직접 퇴직급여채무 계산

    Step 1 (명부 검증) 결과를 사용하거나,
    Excel 파일을 직접 업로드하여 계산할 수 있습니다.

    필수 컬럼:
    - 사원번호
    - 이름
    - 생년월일
    - 입사일
    - 기준급여
    """
    try:
        # 파일 검증 및 파싱
        file_bytes, filename = await validate_upload_file(file)

        registry = get_registry()
        parsed = registry.call_tool("parse_roster", file_bytes=file_bytes)

        if not parsed.get("rows"):
            raise HTTPException(status_code=400, detail="파일에서 데이터를 찾을 수 없습니다.")

        # 헤더와 행 데이터 결합
        headers = parsed.get("headers", [])
        rows = parsed.get("rows", [])

        # 직원 데이터 변환
        employees = []
        errors = []

        for i, row in enumerate(rows):
            try:
                # 행 데이터를 딕셔너리로 변환
                row_dict = dict(zip(headers, row))
                emp = parse_employee_from_dict(row_dict)
                employees.append(emp)
            except Exception as e:
                errors.append(f"행 {i+1}: {str(e)}")

        if not employees:
            raise HTTPException(
                status_code=400,
                detail=f"유효한 직원 데이터가 없습니다. 오류: {errors[:5]}"
            )

        # 보험수리적 가정 설정
        assumptions = ActuarialAssumptions(
            discount_rate=discount_rate,
            salary_growth_rate=salary_growth_rate,
            retirement_age=retirement_age,
            turnover_rate=turnover_rate,
        )

        # 계산 실행
        calculator = IFRS1019Calculator(assumptions)
        result = calculator.calculate(employees)

        return {
            "success": True,
            "filename": filename,
            "parsed_rows": len(rows),
            "calculated_employees": len(employees),
            "parse_errors": errors[:10] if errors else None,
            **result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류: {str(e)}")


@router.get("/assumptions/default")
async def get_default_assumptions():
    """
    기본 보험수리적 가정 조회

    IFRS 1019 계산에 사용되는 기본 가정값을 반환합니다.
    실제 계산 시 회사 상황에 맞게 조정하세요.
    """
    default = ActuarialAssumptions()

    return {
        "assumptions": {
            "discount_rate": {
                "value": default.discount_rate,
                "description": "할인율 (우량회사채 수익률 기준)",
                "unit": "%",
                "display": f"{default.discount_rate * 100}%"
            },
            "salary_growth_rate": {
                "value": default.salary_growth_rate,
                "description": "임금상승률",
                "unit": "%",
                "display": f"{default.salary_growth_rate * 100}%"
            },
            "inflation_rate": {
                "value": default.inflation_rate,
                "description": "물가상승률",
                "unit": "%",
                "display": f"{default.inflation_rate * 100}%"
            },
            "retirement_age": {
                "value": default.retirement_age,
                "description": "정년",
                "unit": "세",
                "display": f"{default.retirement_age}세"
            },
            "mortality_rate": {
                "value": default.mortality_rate,
                "description": "사망률 (연간)",
                "unit": "%",
                "display": f"{default.mortality_rate * 100}%"
            },
            "turnover_rate": {
                "value": default.turnover_rate,
                "description": "퇴직률 (자발적 이직)",
                "unit": "%",
                "display": f"{default.turnover_rate * 100}%"
            },
            "severance_multiplier": {
                "value": default.severance_multiplier,
                "description": "퇴직금 지급률 (근속년수당 월급여)",
                "unit": "배",
                "display": f"{default.severance_multiplier}배"
            },
        },
        "notes": [
            "할인율은 평가기준일 현재 우량회사채 수익률을 참고합니다.",
            "임금상승률은 회사의 과거 급여 인상 추이를 반영합니다.",
            "퇴직률은 자발적 이직률로, 회사 특성에 따라 조정이 필요합니다.",
        ]
    }


@router.get("/assumptions/market")
async def get_market_assumptions():
    """
    시장 참조 보험수리적 가정

    실무에서 자주 사용되는 가정 범위를 제공합니다.
    """
    return {
        "korea_market_2024": {
            "discount_rate": {
                "range": [0.04, 0.055],
                "typical": 0.045,
                "source": "AA- 등급 이상 회사채 수익률"
            },
            "salary_growth_rate": {
                "range": [0.02, 0.05],
                "typical": 0.03,
                "source": "한국 평균 임금상승률"
            },
            "turnover_rate_by_industry": {
                "제조업": 0.03,
                "IT/SW": 0.08,
                "금융": 0.04,
                "서비스": 0.10,
                "건설": 0.06,
            },
            "retirement_age": {
                "legal": 60,
                "actual_average": 57,
            }
        },
        "calculation_methods": {
            "projected_unit_credit": "예측단위적립방식 (IFRS 1019 표준)",
            "current_unit_credit": "현재단위적립방식 (비권장)",
        }
    }
