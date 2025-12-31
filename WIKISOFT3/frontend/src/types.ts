// API 타입 정의 (v3)
export interface DiagnosticQuestion {
  id: string
  category: string
  question: string
  type: 'number' | 'text' | 'choice'
  unit?: string
  choices?: string[]
  mapping?: string
  validate_against?: string
  suggest_from?: string  // AI 기본값 제안용
  format?: string
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
  steps?: {
    parsed_summary?: { headers: string[]; row_count: number }
    matches?: any
    validation?: any
    report?: any
  }
}

export interface AutoValidateResult {
  status: string
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
    anomalies: Array<{ type: string; severity: string; message: string }>
    recommendation: string
  }
  steps: {
    parsed_summary: { headers: string[]; row_count: number }
    matches: any
    validation: { passed: boolean; warnings: string[]; checks: any[] }
    report: any
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
  value?: any
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

// 동적 질문
export interface DynamicQuestion {
  id: string
  question: string
  type: 'confirmation' | 'unmapped_header' | 'ai_question' | 'ai_generated'
  severity: 'error' | 'warning' | 'info' | 'question'
  options: Array<{ value: string; label: string }>
  dynamic: boolean
  required?: boolean
  context?: any
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
