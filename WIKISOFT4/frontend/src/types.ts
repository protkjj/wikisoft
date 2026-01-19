// API 타입 정의 (v4)
export interface DiagnosticQuestion {
  id: string
  category: string
  question: string
  type: 'number' | 'text' | 'choice' | 'date' | 'multiselect' | 'textarea' | 'group'
  unit?: string
  choices?: string[]
  mapping?: string
  validate_against?: string
  suggest_from?: string  // AI 기본값 제안용
  format?: string
  parent?: string        // 상위 질문 ID (하위 항목일 경우)
  subcategory?: string   // 세부 분류
  calculated?: boolean   // 자동 계산 여부 (group 타입일 때)
  condition?: {          // 조건부 질문 - 이전 질문 답변에 따라 표시
    question_id: string  // 참조할 질문 ID
    answer: string       // 이 답변일 때만 현재 질문 표시
  }
}

// 섹션 정의
export interface DiagnosticSection {
  id: number
  title: string
  description: string
  icon: string
  categories: string[]  // 이 섹션에 포함되는 category 목록
}

export interface DiagnosticQuestionsResponse {
  total: number
  questions: DiagnosticQuestion[]
  note?: string
}

export interface ValidationWarning {
  question_id?: string
  severity: 'low' | 'medium' | 'high' | 'warning' | 'info'
  message: string
  user_input?: string
  calculated?: string
  diff?: number
  diff_percent?: number
}

// 검증 에러 (형식/교차 검증)
export interface ValidationError {
  row?: number
  field?: string
  column?: string
  message?: string
  error?: string
  reason?: string
  emp_info?: string
  severity: 'error'
}

// 검증 경고 (상세 정보 포함)
export interface ValidationWarningItem {
  row?: number
  field?: string
  column?: string
  message?: string
  warning?: string
  reason?: string
  emp_info?: string
  severity: 'warning' | 'low' | 'medium' | 'high' | 'info'
  question_id?: string
  user_input?: string
  calculated?: string
  diff?: number
  diff_percent?: number
}

// 검증 체크 결과
export interface ValidationCheck {
  check: string
  passed: boolean
  message?: string
}

// 검증 단계별 결과 타입
export interface ValidationSteps {
  parsed_summary?: {
    headers: string[]
    row_count: number
    all_rows?: Record<string, string | number | null>[]
  }
  matches?: MappingResult
  validation?: {
    passed: boolean
    errors?: ValidationError[]
    warnings?: ValidationWarningItem[]
    checks?: ValidationCheck[]
  }
  report?: {
    summary?: string
    details?: Record<string, string | number | boolean>
  }
}

export interface ValidationResult {
  status: string
  confidence?: {
    score: number
    factors?: Record<string, number>
  }
  anomalies?: {
    detected: boolean
    anomalies: Array<{ type: string; severity: string; message: string }>
    recommendation: string
  }
  steps?: ValidationSteps
}

export interface AutoValidateResult {
  status: string
  session_id?: string  // 세션 ID (다운로드 시 필요)
  confidence: {
    score: number
    factors: {
      match_confidence: number
      error_count: number
      warning_count: number
    }
  }
  anomalies: {
    detected: boolean
    anomalies: Array<{
      type: string
      severity: string
      message: string
      auto_fix?: string
    }>
    recommendation: string
  }
  steps: {
    parsed_summary: {
      headers: string[]
      row_count: number
      all_rows?: Record<string, string | number | null>[]
    }
    matches: MappingResult
    validation: {
      passed: boolean
      errors?: ValidationError[]
      warnings?: ValidationWarningItem[]
      checks?: ValidationCheck[]
    }
    report: {
      summary?: string
      details?: Record<string, string | number | boolean>
    }
  }
}

export interface CompanyInfo {
  company_name: string
  phone: string
  email: string
  작성기준일: string
}

// 수동 매핑 관련 타입
export interface HeaderMatch {
  source: string           // 고객 헤더
  target: string | null    // 표준 필드
  confidence: number       // 0.0~1.0
  unmapped?: boolean       // 매핑 안 됨
  skipped?: boolean        // 의도적으로 건너뛰기 (매핑 안함 선택)
  fallback?: boolean       // 폴백 사용
  used_ai?: boolean        // AI 사용
  reason?: string          // AI 매칭 이유
}

export interface MappingResult {
  columns: string[]
  matches: HeaderMatch[]
  warnings: string[]
  used_ai: boolean
}

export interface StandardField {
  name: string
  description: string
  required: boolean
  aliases: string[]
  sheet: string
}

// 이상 탐지 항목
export interface AnomalyItem {
  type: string
  severity: 'error' | 'warning' | 'info' | 'question' | 'high' | 'medium' | 'low'
  message: string
  field?: string
  row?: number
  value?: string | number | boolean | null
  auto_fix?: string
}

// AI 에이전트 추론 단계
export interface AgentReasoningStep {
  step: number
  thought: string
  action: string
  result_success: boolean
  confidence: number
  error?: string
}

// 동적 질문 컨텍스트
export interface DynamicQuestionContext {
  header?: string
  row?: number
  field?: string
  value?: string | number | null
  suggestion?: string
}

// 동적 질문
export interface DynamicQuestion {
  id: string
  question: string
  type: 'confirmation' | 'unmapped_header' | 'ai_question' | 'ai_generated'
  severity: 'error' | 'warning' | 'info' | 'question'
  options: Array<{ value: string; label: string }>
  dynamic: boolean
  required?: boolean
  context?: DynamicQuestionContext
  reason?: string
}

// AutoValidateResult 확장 (ReACT Agent용)
export interface AutoValidateResultExtended extends AutoValidateResult {
  agent_reasoning?: AgentReasoningStep[]
  agent_explanation?: string
  iterations?: number
  needs_human_review?: boolean
  duplicates?: DuplicateResult  // 중복 탐지 결과 추가
}

// 중복 탐지 결과
export interface DuplicateResult {
  has_duplicates: boolean
  total_duplicates: number
  exact_duplicates: DuplicateItem[]
  similar_duplicates: DuplicateItem[]
  suspicious_duplicates: DuplicateItem[]
  summary: string
}

export interface DuplicateItem {
  type: 'exact' | 'similar' | 'suspicious'
  severity: 'error' | 'warning' | 'info'
  key: string
  key_field: string
  rows: number[]
  count: number
  message: string
  emp_ids?: string[]
}

// Windmill 실행 기록
export interface ValidationRun {
  timestamp: string
  status: string
  action?: string | null
  auto_approve?: boolean | null
  confidence?: number | null
  message?: string | null
  file_url?: string | null
  run_id?: string | null
  flow_id?: string | null
}
