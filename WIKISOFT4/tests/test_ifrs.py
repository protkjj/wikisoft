"""
IFRS 1019 퇴직급여 계산 테스트
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

# Calculator tests
from core.calculators.ifrs1019 import (
    IFRS1019Calculator,
    ActuarialAssumptions,
    EmployeeData,
    EmployeeType,
    PlanType,
    parse_employee_from_dict,
)


class TestActuarialAssumptions:
    """보험수리적 가정 테스트"""

    def test_default_assumptions(self):
        """기본 가정값 테스트"""
        assumptions = ActuarialAssumptions()
        assert assumptions.discount_rate == 0.045
        assert assumptions.salary_growth_rate == 0.03
        assert assumptions.retirement_age == 60
        assert assumptions.turnover_rate == 0.05

    def test_custom_assumptions(self):
        """사용자 정의 가정값 테스트"""
        assumptions = ActuarialAssumptions(
            discount_rate=0.05,
            salary_growth_rate=0.04,
            retirement_age=65,
        )
        assert assumptions.discount_rate == 0.05
        assert assumptions.salary_growth_rate == 0.04
        assert assumptions.retirement_age == 65


class TestEmployeeData:
    """직원 데이터 테스트"""

    def test_employee_creation(self):
        """직원 데이터 생성 테스트"""
        emp = EmployeeData(
            employee_id="E001",
            name="홍길동",
            birth_date=date(1985, 3, 15),
            hire_date=date(2015, 6, 1),
            base_salary=5000000,
        )
        assert emp.employee_id == "E001"
        assert emp.name == "홍길동"
        assert emp.base_salary == 5000000
        assert emp.employee_type == EmployeeType.REGULAR
        assert emp.plan_type == PlanType.DB

    def test_parse_employee_from_dict(self):
        """딕셔너리에서 직원 데이터 파싱 테스트"""
        data = {
            "employee_id": "E002",
            "name": "김영희",
            "birth_date": "1990-07-22",
            "hire_date": "2018-03-01",
            "base_salary": 4500000,
        }
        emp = parse_employee_from_dict(data)
        assert emp.employee_id == "E002"
        assert emp.name == "김영희"
        assert emp.birth_date == date(1990, 7, 22)

    def test_parse_employee_korean_headers(self):
        """한글 헤더 파싱 테스트"""
        data = {
            "사원번호": "E003",
            "이름": "박철수",
            "생년월일": "1988-01-10",
            "입사일": "2016-09-15",
            "기준급여": 4800000,
        }
        emp = parse_employee_from_dict(data)
        assert emp.employee_id == "E003"
        assert emp.name == "박철수"


class TestIFRS1019Calculator:
    """IFRS 1019 계산기 테스트"""

    @pytest.fixture
    def calculator(self):
        """기본 계산기 fixture"""
        return IFRS1019Calculator(ActuarialAssumptions())

    @pytest.fixture
    def sample_employees(self):
        """샘플 직원 데이터 fixture"""
        return [
            EmployeeData(
                employee_id="E001",
                name="홍길동",
                birth_date=date(1985, 3, 15),
                hire_date=date(2015, 6, 1),
                base_salary=5000000,
            ),
            EmployeeData(
                employee_id="E002",
                name="김영희",
                birth_date=date(1990, 7, 22),
                hire_date=date(2018, 3, 1),
                base_salary=4500000,
            ),
        ]

    def test_calculate_single_employee(self, calculator):
        """단일 직원 계산 테스트"""
        emp = EmployeeData(
            employee_id="E001",
            name="테스트",
            birth_date=date(1985, 1, 1),
            hire_date=date(2020, 1, 1),
            base_salary=4000000,
        )
        result = calculator.calculate([emp])

        assert result.total_employees == 1
        assert result.total_dbo > 0
        assert result.total_service_cost > 0
        assert len(result.employees) == 1

    def test_calculate_multiple_employees(self, calculator, sample_employees):
        """다중 직원 계산 테스트"""
        result = calculator.calculate(sample_employees)

        assert result.total_employees == 2
        assert result.total_dbo > 0
        assert len(result.employees) == 2

    def test_dbo_increases_with_service_years(self, calculator):
        """근속년수에 따른 DBO 증가 테스트"""
        # 5년 근속
        emp1 = EmployeeData(
            employee_id="E001",
            name="5년차",
            birth_date=date(1985, 1, 1),
            hire_date=date(2020, 1, 1),
            base_salary=4000000,
        )
        # 10년 근속
        emp2 = EmployeeData(
            employee_id="E002",
            name="10년차",
            birth_date=date(1985, 1, 1),
            hire_date=date(2015, 1, 1),
            base_salary=4000000,
        )

        result1 = calculator.calculate([emp1])
        result2 = calculator.calculate([emp2])

        # 근속년수가 길수록 DBO가 높아야 함
        assert result2.employees[0].dbo > result1.employees[0].dbo

    def test_dbo_increases_with_salary(self, calculator):
        """급여에 따른 DBO 증가 테스트"""
        emp1 = EmployeeData(
            employee_id="E001",
            name="저급여",
            birth_date=date(1985, 1, 1),
            hire_date=date(2018, 1, 1),
            base_salary=3000000,
        )
        emp2 = EmployeeData(
            employee_id="E002",
            name="고급여",
            birth_date=date(1985, 1, 1),
            hire_date=date(2018, 1, 1),
            base_salary=6000000,
        )

        result1 = calculator.calculate([emp1])
        result2 = calculator.calculate([emp2])

        # 급여가 높을수록 DBO가 높아야 함
        assert result2.employees[0].dbo > result1.employees[0].dbo

    def test_projected_salary_calculation(self, calculator):
        """예상급여 계산 테스트"""
        emp = EmployeeData(
            employee_id="E001",
            name="테스트",
            birth_date=date(1995, 1, 1),  # 30세, 정년까지 30년
            hire_date=date(2020, 1, 1),
            base_salary=4000000,
        )
        result = calculator.calculate([emp])

        # 예상급여는 현재급여보다 높아야 함 (임금상승률 적용)
        assert result.employees[0].projected_salary > emp.base_salary

    def test_result_to_dict(self, calculator, sample_employees):
        """결과 딕셔너리 변환 테스트"""
        result = calculator.calculate(sample_employees)
        result_dict = result.to_dict()

        assert "summary" in result_dict
        assert "employees" in result_dict
        assert "assumptions" in result_dict
        assert "metadata" in result_dict


class TestIFRSAPI:
    """IFRS API 엔드포인트 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트 fixture"""
        from api.v4.main import app
        return TestClient(app)

    def test_get_default_assumptions(self, client):
        """기본 가정 조회 테스트"""
        response = client.get("/api/v4/ifrs/assumptions/default")
        assert response.status_code == 200
        data = response.json()
        assert "assumptions" in data
        assert "discount_rate" in data["assumptions"]

    def test_get_market_assumptions(self, client):
        """시장 가정 조회 테스트"""
        response = client.get("/api/v4/ifrs/assumptions/market")
        assert response.status_code == 200
        data = response.json()
        assert "korea_market_2024" in data

    def test_calculate_dbo(self, client):
        """DBO 계산 API 테스트"""
        payload = {
            "employees": [
                {
                    "employee_id": "E001",
                    "name": "홍길동",
                    "birth_date": "1985-03-15",
                    "hire_date": "2015-06-01",
                    "base_salary": 5000000,
                }
            ]
        }
        response = client.post("/api/v4/ifrs/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["total_employees"] == 1
        assert data["summary"]["total_dbo"] > 0

    def test_calculate_with_custom_assumptions(self, client):
        """사용자 정의 가정으로 계산 테스트"""
        payload = {
            "employees": [
                {
                    "employee_id": "E001",
                    "name": "테스트",
                    "birth_date": "1990-01-01",
                    "hire_date": "2020-01-01",
                    "base_salary": 4000000,
                }
            ],
            "assumptions": {
                "discount_rate": 0.05,
                "salary_growth_rate": 0.04,
                "retirement_age": 65,
            }
        }
        response = client.post("/api/v4/ifrs/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["assumptions"]["discount_rate"] == 0.05
        assert data["assumptions"]["retirement_age"] == 65

    def test_calculate_invalid_employee(self, client):
        """잘못된 직원 데이터 테스트"""
        payload = {
            "employees": [
                {
                    "employee_id": "E001",
                    # name 누락
                    "birth_date": "1990-01-01",
                    "hire_date": "2020-01-01",
                    "base_salary": 4000000,
                }
            ]
        }
        response = client.post("/api/v4/ifrs/calculate", json=payload)
        assert response.status_code == 422  # Validation error

    def test_calculate_empty_employees(self, client):
        """빈 직원 목록 테스트"""
        payload = {"employees": []}
        response = client.post("/api/v4/ifrs/calculate", json=payload)
        assert response.status_code == 422  # Validation error (min_length=1)


class TestIFRSEdgeCases:
    """경계 조건 테스트"""

    @pytest.fixture
    def calculator(self):
        return IFRS1019Calculator(ActuarialAssumptions())

    def test_employee_near_retirement(self, calculator):
        """정년 임박 직원 테스트"""
        emp = EmployeeData(
            employee_id="E001",
            name="정년임박",
            birth_date=date(1966, 1, 1),  # 60세
            hire_date=date(2000, 1, 1),
            base_salary=6000000,
        )
        result = calculator.calculate([emp])

        # 정년 임박 시 years_to_retirement가 1 이하
        assert result.employees[0].years_to_retirement <= 1

    def test_new_employee(self, calculator):
        """신입사원 테스트"""
        emp = EmployeeData(
            employee_id="E001",
            name="신입",
            birth_date=date(2000, 1, 1),  # 26세
            hire_date=date(2025, 12, 1),  # 최근 입사
            base_salary=3500000,
        )
        result = calculator.calculate([emp])

        # 신입은 근속년수가 낮고 DBO도 상대적으로 낮음
        assert result.employees[0].service_years < 1
        assert result.employees[0].dbo > 0

    def test_high_salary_executive(self, calculator):
        """고액연봉 임원 테스트"""
        emp = EmployeeData(
            employee_id="E001",
            name="임원",
            birth_date=date(1970, 1, 1),
            hire_date=date(2005, 1, 1),
            base_salary=20000000,  # 2천만원
            employee_type=EmployeeType.EXECUTIVE,
        )
        result = calculator.calculate([emp])

        assert result.employees[0].dbo > 0
        assert result.employees[0].projected_benefit > result.employees[0].dbo
