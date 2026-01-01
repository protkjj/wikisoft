"""
IFRS 1019 퇴직급여 부채 계산 엔진
Projected Unit Credit (PUC) 방식

핵심 개념:
- DBO (Defined Benefit Obligation): 확정급여채무
- Current Service Cost: 당기근무원가
- Interest Cost: 이자비용
- Remeasurement: 재측정요소 (OCI로 인식)
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import math


@dataclass
class Assumptions:
    """계리적 가정"""
    discount_rate: float = 0.045          # 할인율 (AA급 회사채)
    salary_increase_rate: float = 0.03    # 임금상승률
    turnover_rate: float = 0.05           # 이직률 (연간)
    retirement_age: int = 60              # 정년
    benefit_rate: float = 1.0             # 퇴직급여 지급률 (1년당 1개월분 = 1/12)
    mortality_table: str = "KAL2019"      # 사망률 테이블
    valuation_date: date = field(default_factory=date.today)  # 평가기준일


@dataclass
class Employee:
    """직원 정보"""
    employee_id: str
    name: str
    birth_date: date
    hire_date: date
    base_salary: float              # 기준급여 (월급여)
    employee_type: str = "정규직"   # 정규직/임원/계약직
    termination_date: Optional[date] = None
    
    @property
    def age(self) -> float:
        """현재 나이 (소수점)"""
        today = date.today()
        return (today - self.birth_date).days / 365.25
    
    @property
    def service_years(self) -> float:
        """근속연수"""
        end_date = self.termination_date or date.today()
        return (end_date - self.hire_date).days / 365.25
    
    @property
    def years_to_retirement(self) -> float:
        """정년까지 남은 기간"""
        return max(0, 60 - self.age)  # 기본 60세


@dataclass
class DBOResult:
    """DBO 계산 결과"""
    employee_id: str
    name: str
    dbo: float                      # 확정급여채무
    current_service_cost: float     # 당기근무원가
    interest_cost: float            # 이자비용
    projected_benefit: float        # 예상퇴직급여
    service_years: float            # 근속연수
    years_to_retirement: float      # 정년까지 남은 기간
    attribution_ratio: float        # 귀속비율


class IFRSCalculator:
    """IFRS 1019 퇴직급여 계산기"""
    
    def __init__(self, assumptions: Optional[Assumptions] = None):
        self.assumptions = assumptions or Assumptions()
    
    def calculate_projected_salary(self, current_salary: float, years: float) -> float:
        """
        미래 급여 추정 (임금상승률 적용)
        
        Args:
            current_salary: 현재 기준급여
            years: 미래 시점까지 기간
        
        Returns:
            추정 미래 급여
        """
        return current_salary * ((1 + self.assumptions.salary_increase_rate) ** years)
    
    def calculate_survival_probability(self, current_age: float, years: float) -> float:
        """
        생존확률 (간단화된 모델)
        
        실제로는 사망률 테이블 사용해야 함
        여기서는 간단히 연간 생존확률 0.995로 가정
        """
        annual_survival = 0.995
        turnover_survival = 1 - self.assumptions.turnover_rate
        
        # 정년 전까지만 이직률 적용
        if current_age + years < self.assumptions.retirement_age:
            return (annual_survival ** years) * (turnover_survival ** years)
        return annual_survival ** years
    
    def calculate_discount_factor(self, years: float) -> float:
        """
        할인계수 계산
        
        Args:
            years: 할인 기간
        
        Returns:
            할인계수 (현재가치 환산용)
        """
        return 1 / ((1 + self.assumptions.discount_rate) ** years)
    
    def calculate_projected_benefit(self, employee: Employee) -> float:
        """
        예상퇴직급여 계산 (정년 시점)
        
        퇴직급여 = 퇴직시점 월급여 × 근속연수 × 지급률
        """
        years_to_retirement = max(0, self.assumptions.retirement_age - employee.age)
        total_service = employee.service_years + years_to_retirement
        
        projected_salary = self.calculate_projected_salary(
            employee.base_salary,
            years_to_retirement
        )
        
        # 퇴직급여 = 월급여 × 근속연수 (1년당 1개월분)
        return projected_salary * total_service * self.assumptions.benefit_rate
    
    def calculate_dbo(self, employee: Employee) -> DBOResult:
        """
        개인별 DBO (확정급여채무) 계산
        
        PUC 방식:
        DBO = 예상퇴직급여 × (현재근속/총예상근속) × 생존확률 × 할인계수
        """
        # 정년까지 남은 기간
        years_to_retirement = max(0, self.assumptions.retirement_age - employee.age)
        
        # 이미 퇴직한 경우
        if years_to_retirement <= 0:
            projected_benefit = employee.base_salary * employee.service_years * self.assumptions.benefit_rate
            return DBOResult(
                employee_id=employee.employee_id,
                name=employee.name,
                dbo=projected_benefit,
                current_service_cost=0,
                interest_cost=projected_benefit * self.assumptions.discount_rate,
                projected_benefit=projected_benefit,
                service_years=employee.service_years,
                years_to_retirement=0,
                attribution_ratio=1.0
            )
        
        # 예상퇴직급여
        projected_benefit = self.calculate_projected_benefit(employee)
        
        # 총 예상 근속연수
        total_service = employee.service_years + years_to_retirement
        
        # 귀속비율 (현재까지 근속 / 총 예상 근속)
        attribution_ratio = employee.service_years / total_service if total_service > 0 else 0
        
        # 생존확률
        survival_prob = self.calculate_survival_probability(employee.age, years_to_retirement)
        
        # 할인계수
        discount_factor = self.calculate_discount_factor(years_to_retirement)
        
        # DBO = 예상급여 × 귀속비율 × 생존확률 × 할인계수
        dbo = projected_benefit * attribution_ratio * survival_prob * discount_factor
        
        # 당기근무원가 = 예상급여 × (1/총근속) × 생존확률 × 할인계수
        csc_attribution = 1 / total_service if total_service > 0 else 0
        current_service_cost = projected_benefit * csc_attribution * survival_prob * discount_factor
        
        # 이자비용 = 기초 DBO × 할인율 (근사)
        interest_cost = dbo * self.assumptions.discount_rate
        
        return DBOResult(
            employee_id=employee.employee_id,
            name=employee.name,
            dbo=round(dbo, 0),
            current_service_cost=round(current_service_cost, 0),
            interest_cost=round(interest_cost, 0),
            projected_benefit=round(projected_benefit, 0),
            service_years=round(employee.service_years, 2),
            years_to_retirement=round(years_to_retirement, 2),
            attribution_ratio=round(attribution_ratio, 4)
        )
    
    def calculate_batch(self, employees: List[Employee]) -> Dict[str, Any]:
        """
        전체 직원 일괄 계산
        
        Returns:
            - employees: 개인별 계산 결과
            - summary: 합계 및 통계
        """
        results = []
        total_dbo = 0
        total_csc = 0
        total_interest = 0
        
        for emp in employees:
            result = self.calculate_dbo(emp)
            results.append(result)
            total_dbo += result.dbo
            total_csc += result.current_service_cost
            total_interest += result.interest_cost
        
        return {
            "valuation_date": self.assumptions.valuation_date.isoformat(),
            "assumptions": {
                "discount_rate": self.assumptions.discount_rate,
                "salary_increase_rate": self.assumptions.salary_increase_rate,
                "turnover_rate": self.assumptions.turnover_rate,
                "retirement_age": self.assumptions.retirement_age,
                "benefit_rate": self.assumptions.benefit_rate,
            },
            "summary": {
                "total_employees": len(employees),
                "total_dbo": round(total_dbo, 0),
                "total_current_service_cost": round(total_csc, 0),
                "total_interest_cost": round(total_interest, 0),
                "average_dbo_per_employee": round(total_dbo / len(employees), 0) if employees else 0,
            },
            "employees": [
                {
                    "employee_id": r.employee_id,
                    "name": r.name,
                    "dbo": r.dbo,
                    "current_service_cost": r.current_service_cost,
                    "interest_cost": r.interest_cost,
                    "projected_benefit": r.projected_benefit,
                    "service_years": r.service_years,
                    "years_to_retirement": r.years_to_retirement,
                    "attribution_ratio": r.attribution_ratio,
                }
                for r in results
            ]
        }


def parse_employees_from_roster(
    headers: List[str],
    rows: List[List[Any]],
    matches: List[Dict[str, Any]]
) -> List[Employee]:
    """
    검증된 명부 데이터에서 Employee 객체 생성
    
    Args:
        headers: 헤더 리스트
        rows: 데이터 행
        matches: 헤더 매칭 결과
    
    Returns:
        Employee 리스트
    """
    # 매칭 정보로 컬럼 인덱스 찾기
    def find_column(target_field: str) -> Optional[int]:
        for m in matches:
            if m.get("target") == target_field:
                source = m.get("source")
                if source in headers:
                    return headers.index(source)
        return None
    
    # 필드별 컬럼 인덱스
    emp_id_col = find_column("사원번호")
    name_col = find_column("성명")
    birth_col = find_column("생년월일")
    hire_col = find_column("입사일자")
    salary_col = find_column("기준급여")
    type_col = find_column("종업원구분")
    
    employees = []
    
    for row in rows:
        try:
            # 필수 필드 추출
            emp_id = str(row[emp_id_col]) if emp_id_col is not None else ""
            name = str(row[name_col]) if name_col is not None else ""
            
            # 날짜 파싱
            birth_date = _parse_date(row[birth_col]) if birth_col is not None else None
            hire_date = _parse_date(row[hire_col]) if hire_col is not None else None
            
            # 급여 파싱
            base_salary = _parse_number(row[salary_col]) if salary_col is not None else 0
            
            # 종업원구분
            emp_type = str(row[type_col]) if type_col is not None else "정규직"
            
            if emp_id and birth_date and hire_date and base_salary > 0:
                employees.append(Employee(
                    employee_id=emp_id,
                    name=name,
                    birth_date=birth_date,
                    hire_date=hire_date,
                    base_salary=base_salary,
                    employee_type=emp_type
                ))
        except Exception as e:
            # 파싱 실패한 행은 건너뜀
            continue
    
    return employees


def _parse_date(value: Any) -> Optional[date]:
    """날짜 파싱 (다양한 형식 지원)"""
    if value is None:
        return None
    
    if isinstance(value, date):
        return value
    
    if isinstance(value, datetime):
        return value.date()
    
    # 숫자 (Excel 시리얼)
    if isinstance(value, (int, float)):
        try:
            # Excel 시리얼 넘버 변환
            return date.fromordinal(int(value) + 693594)
        except:
            pass
    
    # 문자열
    str_val = str(value).strip()
    
    # YYYYMMDD
    if len(str_val) == 8 and str_val.isdigit():
        try:
            return date(int(str_val[:4]), int(str_val[4:6]), int(str_val[6:8]))
        except:
            pass
    
    # YYYY-MM-DD, YYYY/MM/DD
    for sep in ["-", "/", "."]:
        if sep in str_val:
            parts = str_val.split(sep)
            if len(parts) == 3:
                try:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                except:
                    pass
    
    return None


def _parse_number(value: Any) -> float:
    """숫자 파싱"""
    if value is None:
        return 0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # 문자열에서 숫자 추출
    str_val = str(value).replace(",", "").replace(" ", "").strip()
    
    try:
        return float(str_val)
    except:
        return 0


# 간편 함수
def calculate_ifrs(
    headers: List[str],
    rows: List[List[Any]],
    matches: List[Dict[str, Any]],
    assumptions: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    IFRS 1019 퇴직급여 부채 계산 (간편 함수)
    
    Args:
        headers: 헤더 리스트
        rows: 데이터 행
        matches: 헤더 매칭 결과
        assumptions: 계리적 가정 (선택)
    
    Returns:
        계산 결과 딕셔너리
    """
    # 가정 설정
    if assumptions:
        assum = Assumptions(
            discount_rate=assumptions.get("discount_rate", 0.045),
            salary_increase_rate=assumptions.get("salary_increase_rate", 0.03),
            turnover_rate=assumptions.get("turnover_rate", 0.05),
            retirement_age=assumptions.get("retirement_age", 60),
            benefit_rate=assumptions.get("benefit_rate", 1.0),
        )
    else:
        assum = Assumptions()
    
    # 직원 데이터 파싱
    employees = parse_employees_from_roster(headers, rows, matches)
    
    if not employees:
        return {
            "success": False,
            "error": "유효한 직원 데이터를 찾을 수 없습니다. 필수 필드(사원번호, 생년월일, 입사일자, 기준급여)를 확인해주세요.",
            "parsed_count": 0
        }
    
    # 계산
    calculator = IFRSCalculator(assum)
    result = calculator.calculate_batch(employees)
    result["success"] = True
    result["parsed_count"] = len(employees)
    
    return result
