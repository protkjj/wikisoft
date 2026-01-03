import type { StandardField } from '../types'

// 표준 필드 목록 (백엔드 standard_schema.py와 동기화됨)
export const STANDARD_FIELDS: StandardField[] = [
  { name: '사원번호', description: '직원을 고유하게 식별하는 번호', required: true, aliases: ['직원번호', '사번', 'employee_id'], sheet: '재직자' },
  { name: '이름', description: '직원의 성명 (개인정보 보호로 선택)', required: false, aliases: ['성명', 'name'], sheet: '재직자' },
  { name: '생년월일', description: '직원의 출생일자', required: true, aliases: ['출생일', 'birth_date'], sheet: '재직자' },
  { name: '성별', description: '성별', required: true, aliases: ['gender', 'sex'], sheet: '재직자' },
  { name: '입사일자', description: '회사에 입사한 날짜', required: true, aliases: ['입사일', 'hire_date'], sheet: '재직자' },
  { name: '종업원구분', description: '직원 유형 구분', required: true, aliases: ['직원구분', 'employee_type'], sheet: '재직자' },
  { name: '기준급여', description: '퇴직금 계산 기준 급여', required: true, aliases: ['급여', 'salary'], sheet: '재직자' },
  { name: '제도구분', description: '퇴직연금 제도 유형', required: false, aliases: ['연금제도', 'DB', 'DC'], sheet: '재직자' },
  { name: '퇴직일자', description: '퇴직 날짜', required: false, aliases: ['퇴사일', 'termination_date'], sheet: '퇴직자' },
  { name: '전화번호', description: '연락처', required: false, aliases: ['연락처', 'phone'], sheet: '재직자' },
  { name: '이메일', description: '이메일 주소', required: false, aliases: ['email', 'e-mail'], sheet: '재직자' },
  { name: '부서', description: '소속 부서', required: false, aliases: ['부서명', 'department'], sheet: '재직자' },
  { name: '직급', description: '직급/직책', required: false, aliases: ['직책', 'position'], sheet: '재직자' },
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
