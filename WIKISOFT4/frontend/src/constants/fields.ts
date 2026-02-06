import type { StandardField } from '../types'

// 표준 필드 목록 (백엔드 standard_schema.py와 동기화됨)
export const STANDARD_FIELDS: StandardField[] = [
  {
    name: '사원번호',
    description: '직원을 고유하게 식별하는 번호',
    required: true,
    aliases: ['직원번호', '사번', 'employee_id', 'emp_no', 'emp_id', 'staff_no', '사원코드'],
    sheet: '재직자'
  },
  {
    name: '이름',
    description: '직원의 성명 (개인정보 보호로 선택)',
    required: false,
    aliases: ['성명', 'name', 'full_name', 'employee_name', '직원명'],
    sheet: '재직자'
  },
  {
    name: '생년월일',
    description: '직원의 출생일자',
    required: true,
    aliases: ['출생일', '생일', 'birth_date', 'DOB', 'date_of_birth', 'Birthday'],
    sheet: '재직자'
  },
  {
    name: '성별',
    description: '성별 (남/여, M/F, 1/2 등)',
    required: true,
    aliases: ['gender', 'sex', '성별코드', '성별 (1:남자, 2:여자)', '성별(1:남,2:여)'],
    sheet: '재직자'
  },
  {
    name: '입사일자',
    description: '회사에 입사한 날짜',
    required: true,
    aliases: ['입사일', '입사년월일', '채용일', 'hire_date', 'join_date', 'employment_date', '들어온날짜', '입사날짜'],
    sheet: '재직자'
  },
  {
    name: '종업원구분',
    description: '직원 유형 구분 (임원/직원/계약직 등)',
    required: true,
    aliases: [
      '종업원 구분', '종업원유형', '종업원 유형',
      '종업원 구분 (1:직원, 3:임원, 4:계약직)', '종업원구분 (1:직원, 3:임원, 4:계약직)',
      '직종구분', '직종 구분', '직종구분 (1,2:직원, 3:임원, 4:계약직)',
      '직원구분', '직원 구분', '근로자구분', '근로자 구분',
      '고용형태', '고용 형태', '고용유형', '고용 유형',
      '직급구분', '직급 구분',
      'employee_type', 'emp_type', 'employment_type'
    ],
    sheet: '재직자'
  },
  {
    name: '기준급여',
    description: '퇴직금 계산 기준 급여',
    required: true,
    aliases: ['급여', '월급', 'salary', '기본급', '평균급여', '월평균급여'],
    sheet: '재직자'
  },
  {
    name: '제도구분',
    description: '퇴직연금 제도 유형 (DB/DC/혼합)',
    required: false,
    aliases: ['퇴직제도', '연금제도', 'pension_type', '제도구분 (1,2,3)', 'DB', 'DC'],
    sheet: '재직자'
  },
  {
    name: '당년도퇴직금추계액',
    description: '현재 연도 기준 예상 퇴직금',
    required: true,
    aliases: ['퇴직금추계액', '퇴직금예상액', '퇴직금', 'estimated_retirement', '당년도 퇴직금추계액'],
    sheet: '재직자'
  },
  {
    name: '차년도퇴직금추계액',
    description: '다음 연도 기준 예상 퇴직금',
    required: true,
    aliases: ['내년퇴직금', '차년도퇴직금', '차년도 퇴직금추계액'],
    sheet: '재직자'
  },
  {
    name: '퇴직일',
    description: '퇴직 날짜',
    required: false,
    aliases: ['퇴사일', '퇴직일자', 'DC전환일', '퇴직/전환일', 'resignation_date', 'retire_date', 'termination_date'],
    sheet: '퇴직자'
  },
  {
    name: '전화번호',
    description: '연락처',
    required: false,
    aliases: ['휴대폰', '핸드폰', '전화', 'phone', 'mobile', 'contact', '연락처'],
    sheet: '재직자'
  },
  {
    name: '이메일',
    description: '이메일 주소',
    required: false,
    aliases: ['email', 'e-mail', '메일', '메일주소'],
    sheet: '재직자'
  },
  {
    name: '부서',
    description: '소속 부서',
    required: false,
    aliases: ['부서명', 'department', 'dept', '소속부서', '팀'],
    sheet: '재직자'
  },
  {
    name: '직급',
    description: '직급/직책',
    required: false,
    aliases: ['직책', 'position', 'title', 'rank', '직위'],
    sheet: '재직자'
  },
  {
    name: '적용배수',
    description: '퇴직금 계산 시 적용 배수',
    required: false,
    aliases: ['배수', 'multiplier', '계산배수'],
    sheet: '재직자'
  },
  {
    name: '중간정산기준일',
    description: '중간정산 기준일',
    required: false,
    aliases: ['중간정산일', '정산기준일'],
    sheet: '재직자'
  },
  {
    name: '중간정산액',
    description: '중간정산 금액',
    required: false,
    aliases: ['정산액', '중간정산금액'],
    sheet: '재직자'
  },
]

/**
 * Get array of required field names
 */
export const getRequiredFieldLabels = (): string[] => {
  return STANDARD_FIELDS.filter(f => f.required).map(f => f.name)
}

/**
 * Get array of all field names
 */
export const getAllFieldLabels = (): string[] => {
  return STANDARD_FIELDS.map(f => f.name)
}
