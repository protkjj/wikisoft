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
