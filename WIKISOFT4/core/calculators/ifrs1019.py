"""
IFRS 1019 (K-IFRS 제1019호) 퇴직급여 계산기

종업원급여 회계기준에 따른 퇴직급여채무(DBO) 계산
- Projected Unit Credit (예측단위적립방식) 적용
- 확정급여형(DB) 퇴직연금 계산

참고:
- K-IFRS 제1019호 '종업원급여'
- IAS 19 'Employee Benefits'
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Optional, Dict, Any
import math


class PlanType(str, Enum):
    """퇴직연금 제도 유형"""
    DB = "DB"  # 확정급여형
    DC = "DC"  # 확정기여형
    SEVERANCE = "SEVERANCE"  # 퇴직금 (법정)


class EmployeeType(str, Enum):
    """종업원 구분"""
    EXECUTIVE = "임원"
    REGULAR = "정규직"
    CONTRACT = "계약직"


@dataclass
class ActuarialAssumptions:
    """
    보험수리적 가정

    IFRS 1019에 따른 확정급여채무 측정을 위한 가정
    """
    # 재무적 가정
    discount_rate: float = 0.045  # 할인율 (우량회사채 수익률 기준)
    salary_growth_rate: float = 0.03  # 임금상승률
    inflation_rate: float = 0.02  # 물가상승률

    # 인구통계적 가정
    retirement_age: int = 60  # 정년
    mortality_rate: float = 0.001  # 사망률 (연간)
    turnover_rate: float = 0.05  # 퇴직률 (자발적 이직)
    disability_rate: float = 0.001  # 장해율

    # 급여 관련
    severance_multiplier: float = 1.0  # 퇴직금 지급률 (근속년수당 월급여)

    # 계산 기준일
    valuation_date: date = field(default_factory=date.today)

    def validate(self) -> List[str]:
        """가정값 유효성 검증"""
        errors = []
        if not 0 <= self.discount_rate <= 0.2:
            errors.append(f"할인율이 비정상적입니다: {self.discount_rate}")
        if not 0 <= self.salary_growth_rate <= 0.2:
            errors.append(f"임금상승률이 비정상적입니다: {self.salary_growth_rate}")
        if not 50 <= self.retirement_age <= 70:
            errors.append(f"정년이 비정상적입니다: {self.retirement_age}")
        return errors


@dataclass
class EmployeeData:
    """
    직원 데이터

    퇴직급여 계산에 필요한 직원 정보
    """
    employee_id: str  # 사원번호
    name: str  # 이름
    birth_date: date  # 생년월일
    hire_date: date  # 입사일
    base_salary: int  # 기준급여 (월)

    # 선택 필드
    employee_type: EmployeeType = EmployeeType.REGULAR
    plan_type: PlanType = PlanType.DB
    department: str = ""
    position: str = ""

    # 계산된 필드
    @property
    def age(self) -> int:
        """현재 나이"""
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def service_years(self) -> float:
        """근속년수"""
        today = date.today()
        delta = today - self.hire_date
        return delta.days / 365.25

    @property
    def years_to_retirement(self) -> float:
        """잔여근무년수 (정년 60세 기준)"""
        return max(0, 60 - self.age)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "birth_date": self.birth_date.isoformat(),
            "hire_date": self.hire_date.isoformat(),
            "base_salary": self.base_salary,
            "employee_type": self.employee_type.value,
            "plan_type": self.plan_type.value,
            "age": self.age,
            "service_years": round(self.service_years, 2),
            "years_to_retirement": round(self.years_to_retirement, 2),
        }


@dataclass
class EmployeeResult:
    """직원별 계산 결과"""
    employee_id: str
    name: str
    age: int
    service_years: float
    years_to_retirement: float

    # 계산 결과
    current_salary: int  # 현재 급여
    projected_salary: int  # 퇴직시점 예상급여

    dbo: int  # 확정급여채무 (Defined Benefit Obligation)
    service_cost: int  # 당기근무원가
    interest_cost: int  # 이자원가

    # 상세
    projected_benefit: int  # 예상 퇴직금 (퇴직시점)
    vested_benefit: int  # 기득급여 (현재시점 퇴직시)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "age": self.age,
            "service_years": round(self.service_years, 2),
            "years_to_retirement": round(self.years_to_retirement, 2),
            "current_salary": self.current_salary,
            "projected_salary": self.projected_salary,
            "dbo": self.dbo,
            "service_cost": self.service_cost,
            "interest_cost": self.interest_cost,
            "projected_benefit": self.projected_benefit,
            "vested_benefit": self.vested_benefit,
        }


@dataclass
class CalculationResult:
    """전체 계산 결과"""
    # 요약
    total_employees: int
    total_dbo: int  # 총 확정급여채무
    total_service_cost: int  # 총 당기근무원가
    total_interest_cost: int  # 총 이자원가
    total_projected_benefit: int  # 총 예상퇴직금

    # 가정
    assumptions: Dict[str, Any]

    # 직원별 결과
    employees: List[EmployeeResult]

    # 메타데이터
    calculation_date: str
    version: str = "1.0"

    # 통계
    average_age: float = 0.0
    average_service_years: float = 0.0
    average_dbo: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_employees": self.total_employees,
                "total_dbo": self.total_dbo,
                "total_service_cost": self.total_service_cost,
                "total_interest_cost": self.total_interest_cost,
                "total_projected_benefit": self.total_projected_benefit,
                "average_age": round(self.average_age, 1),
                "average_service_years": round(self.average_service_years, 2),
                "average_dbo": self.average_dbo,
            },
            "assumptions": self.assumptions,
            "employees": [e.to_dict() for e in self.employees],
            "metadata": {
                "calculation_date": self.calculation_date,
                "version": self.version,
            }
        }


class IFRS1019Calculator:
    """
    IFRS 1019 퇴직급여 계산기

    예측단위적립방식(Projected Unit Credit Method)을 사용하여
    확정급여채무(DBO)를 계산합니다.

    사용법:
        calculator = IFRS1019Calculator(assumptions)
        result = calculator.calculate(employees)
    """

    def __init__(self, assumptions: ActuarialAssumptions = None):
        self.assumptions = assumptions or ActuarialAssumptions()

        # 가정 유효성 검증
        errors = self.assumptions.validate()
        if errors:
            raise ValueError(f"보험수리적 가정 오류: {', '.join(errors)}")

    def calculate(self, employees: List[EmployeeData]) -> CalculationResult:
        """
        전체 직원에 대한 퇴직급여채무 계산

        Args:
            employees: 직원 데이터 리스트

        Returns:
            CalculationResult: 계산 결과
        """
        results = []

        for emp in employees:
            if emp.plan_type == PlanType.DC:
                # DC형은 별도 처리 (단순 비용 인식)
                result = self._calculate_dc(emp)
            else:
                # DB형 및 법정퇴직금
                result = self._calculate_db(emp)

            results.append(result)

        # 합계 계산
        total_dbo = sum(r.dbo for r in results)
        total_service_cost = sum(r.service_cost for r in results)
        total_interest_cost = sum(r.interest_cost for r in results)
        total_projected = sum(r.projected_benefit for r in results)

        # 평균 계산
        n = len(results) if results else 1
        avg_age = sum(r.age for r in results) / n if results else 0
        avg_service = sum(r.service_years for r in results) / n if results else 0
        avg_dbo = total_dbo // n if results else 0

        return CalculationResult(
            total_employees=len(employees),
            total_dbo=total_dbo,
            total_service_cost=total_service_cost,
            total_interest_cost=total_interest_cost,
            total_projected_benefit=total_projected,
            assumptions=self._assumptions_to_dict(),
            employees=results,
            calculation_date=datetime.now().isoformat(),
            average_age=avg_age,
            average_service_years=avg_service,
            average_dbo=avg_dbo,
        )

    def _calculate_db(self, emp: EmployeeData) -> EmployeeResult:
        """
        확정급여형(DB) 퇴직급여채무 계산

        예측단위적립방식(PUC):
        1. 퇴직시점 예상급여 산정 (임금상승률 적용)
        2. 예상 퇴직금 계산
        3. 근무기간 비례 배분
        4. 현재가치 할인
        """
        a = self.assumptions

        # 기본 정보
        current_salary = emp.base_salary
        service_years = max(emp.service_years, 0)
        years_to_retire = max(emp.years_to_retirement, 0)
        total_service = service_years + years_to_retire

        # 1. 퇴직시점 예상 급여 (임금상승률 적용)
        projected_salary = int(
            current_salary * ((1 + a.salary_growth_rate) ** years_to_retire)
        )

        # 2. 예상 퇴직금 (퇴직시점)
        # 퇴직금 = 퇴직시점월급여 × 근속년수 × 지급률
        projected_benefit = int(
            projected_salary * total_service * a.severance_multiplier
        )

        # 3. 기득급여 (현재 퇴직 시)
        vested_benefit = int(
            current_salary * service_years * a.severance_multiplier
        )

        # 4. 확정급여채무 (DBO) - 예측단위적립방식
        # DBO = 예상퇴직금 × (현재근속/예상총근속) × 현가계수
        if total_service > 0:
            attribution_ratio = service_years / total_service
        else:
            attribution_ratio = 1.0

        # 현가계수 (할인)
        pv_factor = (1 + a.discount_rate) ** (-years_to_retire) if years_to_retire > 0 else 1.0

        # 생존확률 (사망률, 퇴직률 고려)
        survival_prob = ((1 - a.mortality_rate) * (1 - a.turnover_rate)) ** years_to_retire

        dbo = int(projected_benefit * attribution_ratio * pv_factor * survival_prob)

        # 5. 당기근무원가 (Service Cost)
        # 1년간 추가 적립분
        if total_service > 0:
            unit_credit = projected_benefit / total_service
        else:
            unit_credit = 0
        service_cost = int(unit_credit * pv_factor * survival_prob)

        # 6. 이자원가 (Interest Cost)
        # 기초 DBO에 대한 이자
        interest_cost = int(dbo * a.discount_rate)

        return EmployeeResult(
            employee_id=emp.employee_id,
            name=emp.name,
            age=emp.age,
            service_years=service_years,
            years_to_retirement=years_to_retire,
            current_salary=current_salary,
            projected_salary=projected_salary,
            dbo=dbo,
            service_cost=service_cost,
            interest_cost=interest_cost,
            projected_benefit=projected_benefit,
            vested_benefit=vested_benefit,
        )

    def _calculate_dc(self, emp: EmployeeData) -> EmployeeResult:
        """
        확정기여형(DC) 계산

        DC형은 부채가 없고 기여금만 비용으로 인식
        (여기서는 정보 제공 목적으로 계산)
        """
        current_salary = emp.base_salary

        # DC형 연간 기여금 (급여의 1/12 = 퇴직금 충당금 상당액)
        annual_contribution = current_salary  # 월급여 = 연간 기여금

        return EmployeeResult(
            employee_id=emp.employee_id,
            name=emp.name,
            age=emp.age,
            service_years=emp.service_years,
            years_to_retirement=emp.years_to_retirement,
            current_salary=current_salary,
            projected_salary=current_salary,  # DC는 예측하지 않음
            dbo=0,  # DC는 부채 없음
            service_cost=annual_contribution,  # 연간 기여금 = 비용
            interest_cost=0,
            projected_benefit=0,
            vested_benefit=int(current_salary * emp.service_years),
        )

    def _assumptions_to_dict(self) -> Dict[str, Any]:
        """가정을 딕셔너리로 변환"""
        a = self.assumptions
        return {
            "discount_rate": a.discount_rate,
            "salary_growth_rate": a.salary_growth_rate,
            "inflation_rate": a.inflation_rate,
            "retirement_age": a.retirement_age,
            "mortality_rate": a.mortality_rate,
            "turnover_rate": a.turnover_rate,
            "severance_multiplier": a.severance_multiplier,
            "valuation_date": a.valuation_date.isoformat(),
        }


def parse_employee_from_dict(data: Dict[str, Any]) -> EmployeeData:
    """딕셔너리에서 EmployeeData 생성"""

    def parse_date(value: Any) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            # 다양한 날짜 형식 지원
            for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y.%m.%d", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"날짜 형식을 파싱할 수 없습니다: {value}")
        raise ValueError(f"지원하지 않는 날짜 타입: {type(value)}")

    # 종업원 구분 파싱
    emp_type_str = data.get("employee_type", data.get("종업원구분", "정규직"))
    emp_type = EmployeeType.REGULAR
    if emp_type_str in ["임원", "EXECUTIVE"]:
        emp_type = EmployeeType.EXECUTIVE
    elif emp_type_str in ["계약직", "CONTRACT"]:
        emp_type = EmployeeType.CONTRACT

    # 제도 구분 파싱
    plan_type_str = data.get("plan_type", data.get("제도구분", "DB"))
    plan_type = PlanType.DB
    if plan_type_str in ["DC", "확정기여"]:
        plan_type = PlanType.DC
    elif plan_type_str in ["SEVERANCE", "퇴직금"]:
        plan_type = PlanType.SEVERANCE

    return EmployeeData(
        employee_id=str(data.get("employee_id", data.get("사원번호", ""))),
        name=str(data.get("name", data.get("이름", ""))),
        birth_date=parse_date(data.get("birth_date", data.get("생년월일"))),
        hire_date=parse_date(data.get("hire_date", data.get("입사일"))),
        base_salary=int(data.get("base_salary", data.get("기준급여", 0))),
        employee_type=emp_type,
        plan_type=plan_type,
        department=str(data.get("department", data.get("부서", ""))),
        position=str(data.get("position", data.get("직위", ""))),
    )
